use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Transfer};

declare_id!("FuTsTar11111111111111111111111111111111111");

#[program]
pub mod futstar_momentum_trading {
    use super::*;

    /// Initialize a new momentum trading pool for a match
    pub fn initialize_pool(
        ctx: Context<InitializePool>,
        match_id: String,
        start_time: i64,
        home_team: String,
        away_team: String,
    ) -> Result<()> {
        let pool = &mut ctx.accounts.momentum_pool;
        
        pool.authority = ctx.accounts.authority.key();
        pool.match_id = match_id;
        pool.start_time = start_time;
        pool.home_team = home_team;
        pool.away_team = away_team;
        pool.total_long_volume = 0;
        pool.total_short_volume = 0;
        pool.current_momentum_index = 50; // Start at neutral
        pool.is_active = true;
        pool.created_at = Clock::get()?.unix_timestamp;
        
        msg!("Momentum pool initialized for match: {}", pool.match_id);
        Ok(())
    }

    /// Open a long position (bet on momentum increase)
    pub fn open_long_position(
        ctx: Context<OpenPosition>,
        amount: u64,
        window_duration: i64, // in seconds (300 for 5 minutes)
    ) -> Result<()> {
        let position = &mut ctx.accounts.trading_position;
        let pool = &mut ctx.accounts.momentum_pool;
        let clock = Clock::get()?;
        
        require!(pool.is_active, TradingError::PoolNotActive);
        require!(amount > 0, TradingError::InvalidAmount);
        
        // Transfer tokens from user to pool
        token::transfer(
            CpiContext::new(
                ctx.accounts.token_program.to_account_info(),
                Transfer {
                    from: ctx.accounts.user_token_account.to_account_info(),
                    to: ctx.accounts.pool_token_account.to_account_info(),
                    authority: ctx.accounts.user.to_account_info(),
                },
            ),
            amount,
        )?;
        
        position.trader = ctx.accounts.user.key();
        position.pool = pool.key();
        position.position_type = PositionType::Long;
        position.amount = amount;
        position.entry_momentum_index = pool.current_momentum_index;
        position.entry_time = clock.unix_timestamp;
        position.window_end_time = clock.unix_timestamp + window_duration;
        position.is_settled = false;
        position.pnl = 0;
        
        pool.total_long_volume += amount;
        
        msg!("Long position opened: {} SOL at momentum index {}", 
             amount as f64 / 1e9 as f64, 
             position.entry_momentum_index);
        
        Ok(())
    }

    /// Open a short position (bet on momentum decrease)
    pub fn open_short_position(
        ctx: Context<OpenPosition>,
        amount: u64,
        window_duration: i64,
    ) -> Result<()> {
        let position = &mut ctx.accounts.trading_position;
        let pool = &mut ctx.accounts.momentum_pool;
        let clock = Clock::get()?;
        
        require!(pool.is_active, TradingError::PoolNotActive);
        require!(amount > 0, TradingError::InvalidAmount);
        
        // Transfer tokens from user to pool
        token::transfer(
            CpiContext::new(
                ctx.accounts.token_program.to_account_info(),
                Transfer {
                    from: ctx.accounts.user_token_account.to_account_info(),
                    to: ctx.accounts.pool_token_account.to_account_info(),
                    authority: ctx.accounts.user.to_account_info(),
                },
            ),
            amount,
        )?;
        
        position.trader = ctx.accounts.user.key();
        position.pool = pool.key();
        position.position_type = PositionType::Short;
        position.amount = amount;
        position.entry_momentum_index = pool.current_momentum_index;
        position.entry_time = clock.unix_timestamp;
        position.window_end_time = clock.unix_timestamp + window_duration;
        position.is_settled = false;
        position.pnl = 0;
        
        pool.total_short_volume += amount;
        
        msg!("Short position opened: {} SOL at momentum index {}", 
             amount as f64 / 1e9 as f64, 
             position.entry_momentum_index);
        
        Ok(())
    }

    /// Update momentum index from oracle
    pub fn update_momentum_index(
        ctx: Context<UpdateMomentum>,
        new_index: u8,
    ) -> Result<()> {
        let pool = &mut ctx.accounts.momentum_pool;
        
        require!(ctx.accounts.oracle.key() == pool.authority, TradingError::UnauthorizedOracle);
        require!(new_index <= 100, TradingError::InvalidMomentumIndex);
        
        let old_index = pool.current_momentum_index;
        pool.current_momentum_index = new_index;
        pool.last_update = Clock::get()?.unix_timestamp;
        
        msg!("Momentum index updated: {} -> {}", old_index, new_index);
        
        emit!(MomentumUpdateEvent {
            match_id: pool.match_id.clone(),
            old_index,
            new_index,
            timestamp: pool.last_update,
        });
        
        Ok(())
    }

    /// Settle a position after window ends
    pub fn settle_position(ctx: Context<SettlePosition>) -> Result<()> {
        let position = &mut ctx.accounts.trading_position;
        let pool = &ctx.accounts.momentum_pool;
        let clock = Clock::get()?;
        
        require!(!position.is_settled, TradingError::AlreadySettled);
        require!(clock.unix_timestamp >= position.window_end_time, TradingError::WindowNotEnded);
        
        let momentum_change = pool.current_momentum_index as i16 - position.entry_momentum_index as i16;
        let mut payout = 0u64;
        
        match position.position_type {
            PositionType::Long => {
                if momentum_change > 0 {
                    // Long position wins if momentum increased
                    let profit_multiplier = momentum_change.abs() as u64;
                    payout = position.amount + (position.amount * profit_multiplier / 100);
                    // Apply 2% fee on profits
                    let fee = (payout - position.amount) * 2 / 100;
                    payout -= fee;
                }
            },
            PositionType::Short => {
                if momentum_change < 0 {
                    // Short position wins if momentum decreased
                    let profit_multiplier = momentum_change.abs() as u64;
                    payout = position.amount + (position.amount * profit_multiplier / 100);
                    // Apply 2% fee on profits
                    let fee = (payout - position.amount) * 2 / 100;
                    payout -= fee;
                }
            }
        }
        
        if payout > 0 {
            // Transfer winnings to user
            token::transfer(
                CpiContext::new_with_signer(
                    ctx.accounts.token_program.to_account_info(),
                    Transfer {
                        from: ctx.accounts.pool_token_account.to_account_info(),
                        to: ctx.accounts.user_token_account.to_account_info(),
                        authority: pool.to_account_info(),
                    },
                    &[&[
                        b"momentum_pool",
                        pool.match_id.as_bytes(),
                        &[ctx.bumps.momentum_pool],
                    ]],
                ),
                payout,
            )?;
        }
        
        position.is_settled = true;
        position.pnl = payout as i64 - position.amount as i64;
        position.exit_momentum_index = pool.current_momentum_index;
        position.settled_at = clock.unix_timestamp;
        
        msg!("Position settled. PnL: {} SOL", position.pnl as f64 / 1e9 as f64);
        
        emit!(PositionSettledEvent {
            trader: position.trader,
            position_type: position.position_type.clone(),
            pnl: position.pnl,
            entry_index: position.entry_momentum_index,
            exit_index: position.exit_momentum_index,
        });
        
        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(match_id: String)]
pub struct InitializePool<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + MomentumPool::LEN,
        seeds = [b"momentum_pool", match_id.as_bytes()],
        bump
    )]
    pub momentum_pool: Account<'info, MomentumPool>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct OpenPosition<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + TradingPosition::LEN,
        seeds = [
            b"position",
            momentum_pool.key().as_ref(),
            user.key().as_ref(),
            &Clock::get()?.unix_timestamp.to_le_bytes()
        ],
        bump
    )]
    pub trading_position: Account<'info, TradingPosition>,
    
    #[account(mut)]
    pub momentum_pool: Account<'info, MomentumPool>,
    
    #[account(mut)]
    pub user: Signer<'info>,
    
    #[account(mut)]
    pub user_token_account: Account<'info, TokenAccount>,
    
    #[account(mut)]
    pub pool_token_account: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateMomentum<'info> {
    #[account(mut)]
    pub momentum_pool: Account<'info, MomentumPool>,
    
    pub oracle: Signer<'info>,
}

#[derive(Accounts)]
pub struct SettlePosition<'info> {
    #[account(mut)]
    pub trading_position: Account<'info, TradingPosition>,
    
    #[account(
        seeds = [b"momentum_pool", momentum_pool.match_id.as_bytes()],
        bump
    )]
    pub momentum_pool: Account<'info, MomentumPool>,
    
    #[account(mut)]
    pub user_token_account: Account<'info, TokenAccount>,
    
    #[account(mut)]
    pub pool_token_account: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
}

#[account]
pub struct MomentumPool {
    pub authority: Pubkey,
    pub match_id: String,
    pub start_time: i64,
    pub home_team: String,
    pub away_team: String,
    pub total_long_volume: u64,
    pub total_short_volume: u64,
    pub current_momentum_index: u8,
    pub is_active: bool,
    pub created_at: i64,
    pub last_update: i64,
}

impl MomentumPool {
    pub const LEN: usize = 32 + 64 + 8 + 32 + 32 + 8 + 8 + 1 + 1 + 8 + 8 + 128; // Buffer for strings
}

#[account]
pub struct TradingPosition {
    pub trader: Pubkey,
    pub pool: Pubkey,
    pub position_type: PositionType,
    pub amount: u64,
    pub entry_momentum_index: u8,
    pub exit_momentum_index: u8,
    pub entry_time: i64,
    pub window_end_time: i64,
    pub is_settled: bool,
    pub pnl: i64,
    pub settled_at: i64,
}

impl TradingPosition {
    pub const LEN: usize = 32 + 32 + 1 + 8 + 1 + 1 + 8 + 8 + 1 + 8 + 8;
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug)]
pub enum PositionType {
    Long,
    Short,
}

#[event]
pub struct MomentumUpdateEvent {
    pub match_id: String,
    pub old_index: u8,
    pub new_index: u8,
    pub timestamp: i64,
}

#[event]
pub struct PositionSettledEvent {
    pub trader: Pubkey,
    pub position_type: PositionType,
    pub pnl: i64,
    pub entry_index: u8,
    pub exit_index: u8,
}

#[error_code]
pub enum TradingError {
    #[msg("Pool is not active")]
    PoolNotActive,
    #[msg("Invalid amount")]
    InvalidAmount,
    #[msg("Unauthorized oracle")]
    UnauthorizedOracle,
    #[msg("Invalid momentum index")]
    InvalidMomentumIndex,
    #[msg("Position already settled")]
    AlreadySettled,
    #[msg("Trading window has not ended")]
    WindowNotEnded,
}
