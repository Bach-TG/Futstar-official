import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Dimensions,
  ActivityIndicator,
  Modal,
  TextInput,
  Alert,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { useWallet } from '@solana/wallet-adapter-react';
import { Connection, PublicKey, Transaction } from '@solana/web3.js';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// Types
interface MatchData {
  match_id: string;
  home_team: { name: string; logo_url: string };
  away_team: { name: string; logo_url: string };
  current_minute: number;
  score_home: number;
  score_away: number;
}

interface MomentumData {
  timestamp: string;
  momentum_index: number;
  possession: number;
  shots_home: number;
  shots_away: number;
  xg_home: number;
  xg_away: number;
}

interface Position {
  type: 'long' | 'short';
  amount: number;
  entryIndex: number;
  entryTime: Date;
}

const MomentumTradingScreen: React.FC = () => {
  // State Management
  const [selectedMatch, setSelectedMatch] = useState<MatchData | null>(null);
  const [momentumHistory, setMomentumHistory] = useState<number[]>([50]);
  const [currentMomentum, setCurrentMomentum] = useState<MomentumData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [tradeAmount, setTradeAmount] = useState('');
  const [tradeType, setTradeType] = useState<'long' | 'short'>('long');
  const [userPositions, setUserPositions] = useState<Position[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const wallet = useWallet();

  // WebSocket connection for real-time momentum updates
  useEffect(() => {
    if (selectedMatch) {
      const websocket = new WebSocket(
        `ws://localhost:8000/ws/momentum/${selectedMatch.match_id}`
      );

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'momentum_update') {
          const momentum = data.data;
          setCurrentMomentum(momentum);
          setMomentumHistory((prev) => {
            const updated = [...prev, momentum.momentum_index];
            // Keep only last 60 data points (1 minute of data)
            return updated.slice(-60);
          });
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      setWs(websocket);

      return () => {
        websocket.close();
      };
    }
  }, [selectedMatch]);

  // Fetch live matches
  const fetchLiveMatches = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/matches');
      const matches = await response.json();
      if (matches.length > 0) {
        setSelectedMatch(matches[0]);
      }
    } catch (error) {
      console.error('Error fetching matches:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLiveMatches();
  }, []);

  // Open trading position
  const openPosition = async () => {
    if (!wallet.publicKey || !selectedMatch) {
      Alert.alert('Error', 'Please connect your wallet first');
      return;
    }

    const amount = parseFloat(tradeAmount);
    if (isNaN(amount) || amount <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/positions/open', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          match_id: selectedMatch.match_id,
          position_type: tradeType,
          amount: amount,
          wallet_address: wallet.publicKey.toString(),
          window_duration: 300, // 5 minutes
        }),
      });

      if (response.ok) {
        const position = await response.json();
        setUserPositions([...userPositions, {
          type: tradeType,
          amount: amount,
          entryIndex: position.entry_index,
          entryTime: new Date(position.entry_time),
        }]);
        
        Alert.alert(
          'Position Opened',
          `${tradeType.toUpperCase()} position opened for ${amount} SOL at momentum ${position.entry_index}`
        );
        setShowTradeModal(false);
        setTradeAmount('');
      }
    } catch (error) {
      console.error('Error opening position:', error);
      Alert.alert('Error', 'Failed to open position');
    } finally {
      setIsLoading(false);
    }
  };

  // Chart configuration
  const chartConfig = {
    backgroundColor: '#1a1d29',
    backgroundGradientFrom: '#1a1d29',
    backgroundGradientTo: '#2a2d3a',
    decimalPlaces: 0,
    color: (opacity = 1) => {
      const lastIndex = momentumHistory[momentumHistory.length - 1];
      const prevIndex = momentumHistory[momentumHistory.length - 2] || 50;
      return lastIndex > prevIndex
        ? `rgba(34, 197, 94, ${opacity})` // Green for up
        : `rgba(239, 68, 68, ${opacity})`; // Red for down
    },
    labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: '#ffa726',
    },
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Futstar ⚽</Text>
        <Text style={styles.subtitle}>Momentum Trading</Text>
      </View>

      {/* Match Info */}
      {selectedMatch && (
        <View style={styles.matchCard}>
          <View style={styles.matchInfo}>
            <View style={styles.teamInfo}>
              <Text style={styles.teamName}>{selectedMatch.home_team.name}</Text>
              <Text style={styles.score}>{selectedMatch.score_home}</Text>
            </View>
            <View style={styles.matchTime}>
              <Text style={styles.minute}>{selectedMatch.current_minute}'</Text>
              <Text style={styles.status}>LIVE</Text>
            </View>
            <View style={styles.teamInfo}>
              <Text style={styles.score}>{selectedMatch.score_away}</Text>
              <Text style={styles.teamName}>{selectedMatch.away_team.name}</Text>
            </View>
          </View>
        </View>
      )}

      {/* Momentum Chart */}
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Match Momentum</Text>
        <LineChart
          data={{
            labels: [],
            datasets: [
              {
                data: momentumHistory.length > 0 ? momentumHistory : [50],
              },
            ],
          }}
          width={screenWidth - 32}
          height={200}
          yAxisInterval={1}
          chartConfig={chartConfig}
          bezier
          style={styles.chart}
          withInnerLines={false}
          withOuterLines={true}
          withVerticalLines={false}
          withHorizontalLines={true}
          withVerticalLabels={false}
          withHorizontalLabels={true}
          getDotColor={(dataPoint) => {
            if (dataPoint > 50) return '#22c55e';
            if (dataPoint < 50) return '#ef4444';
            return '#fbbf24';
          }}
        />
        
        {/* Momentum Indicator */}
        <View style={styles.momentumIndicator}>
          <Text style={styles.momentumLabel}>Current Momentum</Text>
          <Text style={[
            styles.momentumValue,
            { color: currentMomentum?.momentum_index > 50 ? '#22c55e' : '#ef4444' }
          ]}>
            {currentMomentum?.momentum_index || 50}
          </Text>
        </View>
      </View>

      {/* Stats Grid */}
      {currentMomentum && (
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Possession</Text>
            <Text style={styles.statValue}>{currentMomentum.possession.toFixed(0)}%</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Shots</Text>
            <Text style={styles.statValue}>
              {currentMomentum.shots_home} - {currentMomentum.shots_away}
            </Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>xG</Text>
            <Text style={styles.statValue}>
              {currentMomentum.xg_home.toFixed(2)} - {currentMomentum.xg_away.toFixed(2)}
            </Text>
          </View>
        </View>
      )}

      {/* Trading Buttons */}
      <View style={styles.tradingButtons}>
        <TouchableOpacity
          style={[styles.tradeButton, styles.longButton]}
          onPress={() => {
            setTradeType('long');
            setShowTradeModal(true);
          }}
        >
          <Text style={styles.tradeButtonText}>📈 GO LONG</Text>
          <Text style={styles.tradeButtonSubtext}>Bet on momentum ↑</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tradeButton, styles.shortButton]}
          onPress={() => {
            setTradeType('short');
            setShowTradeModal(true);
          }}
        >
          <Text style={styles.tradeButtonText}>📉 GO SHORT</Text>
          <Text style={styles.tradeButtonSubtext}>Bet on momentum ↓</Text>
        </TouchableOpacity>
      </View>

      {/* Active Positions */}
      {userPositions.length > 0 && (
        <View style={styles.positionsContainer}>
          <Text style={styles.positionsTitle}>Active Positions</Text>
          {userPositions.map((position, index) => (
            <View key={index} style={styles.positionCard}>
              <View style={styles.positionInfo}>
                <Text style={styles.positionType}>
                  {position.type.toUpperCase()}
                </Text>
                <Text style={styles.positionAmount}>{position.amount} SOL</Text>
              </View>
              <View style={styles.positionStats}>
                <Text style={styles.positionEntry}>Entry: {position.entryIndex}</Text>
                <Text style={styles.positionTime}>
                  {new Date(position.entryTime).toLocaleTimeString()}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Trade Modal */}
      <Modal
        visible={showTradeModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowTradeModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>
              Open {tradeType.toUpperCase()} Position
            </Text>
            
            <Text style={styles.modalLabel}>Amount (SOL)</Text>
            <TextInput
              style={styles.modalInput}
              value={tradeAmount}
              onChangeText={setTradeAmount}
              placeholder="0.00"
              keyboardType="decimal-pad"
              placeholderTextColor="#666"
            />
            
            <Text style={styles.modalInfo}>
              Window Duration: 5 minutes{'\n'}
              Fee: 2% on profits
            </Text>
            
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setShowTradeModal(false)}
              >
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[
                  styles.modalButton,
                  tradeType === 'long' ? styles.confirmLongButton : styles.confirmShortButton
                ]}
                onPress={openPosition}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.modalButtonText}>Confirm</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f1419',
  },
  header: {
    padding: 20,
    paddingTop: 50,
    backgroundColor: '#1a1d29',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 16,
    color: '#9ca3af',
    marginTop: 4,
  },
  matchCard: {
    backgroundColor: '#1a1d29',
    margin: 16,
    padding: 16,
    borderRadius: 12,
  },
  matchInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  teamInfo: {
    alignItems: 'center',
  },
  teamName: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  score: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 8,
  },
  matchTime: {
    alignItems: 'center',
  },
  minute: {
    color: '#22c55e',
    fontSize: 18,
    fontWeight: 'bold',
  },
  status: {
    color: '#22c55e',
    fontSize: 12,
    marginTop: 4,
  },
  chartContainer: {
    backgroundColor: '#1a1d29',
    margin: 16,
    padding: 16,
    borderRadius: 12,
  },
  chartTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  momentumIndicator: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
    padding: 12,
    backgroundColor: '#2a2d3a',
    borderRadius: 8,
  },
  momentumLabel: {
    color: '#9ca3af',
    fontSize: 14,
  },
  momentumValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginHorizontal: 16,
    marginBottom: 16,
  },
  statCard: {
    backgroundColor: '#1a1d29',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 4,
  },
  statLabel: {
    color: '#9ca3af',
    fontSize: 12,
    marginBottom: 4,
  },
  statValue: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  tradingButtons: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginBottom: 16,
  },
  tradeButton: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  longButton: {
    backgroundColor: '#22c55e',
  },
  shortButton: {
    backgroundColor: '#ef4444',
  },
  tradeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  tradeButtonSubtext: {
    color: '#fff',
    fontSize: 12,
    marginTop: 4,
    opacity: 0.8,
  },
  positionsContainer: {
    margin: 16,
  },
  positionsTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  positionCard: {
    backgroundColor: '#1a1d29',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  positionInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  positionType: {
    color: '#fff',
    fontWeight: '600',
  },
  positionAmount: {
    color: '#fff',
  },
  positionStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  positionEntry: {
    color: '#9ca3af',
    fontSize: 12,
  },
  positionTime: {
    color: '#9ca3af',
    fontSize: 12,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#1a1d29',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxWidth: 400,
  },
  modalTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  modalLabel: {
    color: '#9ca3af',
    fontSize: 14,
    marginBottom: 8,
  },
  modalInput: {
    backgroundColor: '#2a2d3a',
    color: '#fff',
    padding: 12,
    borderRadius: 8,
    fontSize: 18,
    marginBottom: 16,
  },
  modalInfo: {
    color: '#9ca3af',
    fontSize: 12,
    marginBottom: 20,
    lineHeight: 18,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  cancelButton: {
    backgroundColor: '#4b5563',
  },
  confirmLongButton: {
    backgroundColor: '#22c55e',
  },
  confirmShortButton: {
    backgroundColor: '#ef4444',
  },
  modalButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
});

export default MomentumTradingScreen;
