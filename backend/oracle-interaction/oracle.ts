/**
 * Program IDL in camelCase format in order to be used in JS/TS.
 *
 * Note that this is only a type helper and is not the actual IDL. The original
 * IDL can be found at `target/idl/oracle.json`.
 */
export type Oracle = {
  "address": "4gh2quPxDSyQx39GPSfU86rGcg6gcygux4dUZhD9aC9n",
  "metadata": {
    "name": "oracle",
    "version": "0.1.0",
    "spec": "0.1.0",
    "description": "Created with Anchor"
  },
  "instructions": [
    {
      "name": "closeScoreGroup",
      "discriminator": [
        173,
        70,
        198,
        106,
        196,
        75,
        85,
        21
      ],
      "accounts": [
        {
          "name": "signer",
          "writable": true,
          "signer": true
        },
        {
          "name": "globalConfig",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  103,
                  108,
                  111,
                  98,
                  97,
                  108,
                  45,
                  99,
                  111,
                  110,
                  102,
                  105,
                  103
                ]
              }
            ]
          }
        },
        {
          "name": "scoreGroup",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  103,
                  108,
                  111,
                  98,
                  97,
                  108,
                  45,
                  99,
                  111,
                  110,
                  102,
                  105,
                  103
                ]
              },
              {
                "kind": "account",
                "path": "scoreGroup"
              }
            ]
          }
        }
      ],
      "args": []
    },
    {
      "name": "endMatch",
      "discriminator": [
        34,
        116,
        122,
        191,
        100,
        222,
        20,
        117
      ],
      "accounts": [
        {
          "name": "validator",
          "writable": true,
          "signer": true
        },
        {
          "name": "globalConfig",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  103,
                  108,
                  111,
                  98,
                  97,
                  108,
                  45,
                  99,
                  111,
                  110,
                  102,
                  105,
                  103
                ]
              }
            ]
          }
        },
        {
          "name": "scoreGroup",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  115,
                  99,
                  111,
                  114,
                  101,
                  45,
                  103,
                  114,
                  111,
                  117,
                  112
                ]
              },
              {
                "kind": "arg",
                "path": "scoreGroupId"
              }
            ]
          }
        }
      ],
      "args": [
        {
          "name": "matchId",
          "type": "u64"
        }
      ]
    },
    {
      "name": "initGlobalConfig",
      "discriminator": [
        140,
        136,
        214,
        48,
        87,
        0,
        120,
        255
      ],
      "accounts": [
        {
          "name": "signer",
          "writable": true,
          "signer": true
        },
        {
          "name": "globalConfig",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  103,
                  108,
                  111,
                  98,
                  97,
                  108,
                  45,
                  99,
                  111,
                  110,
                  102,
                  105,
                  103
                ]
              }
            ]
          }
        },
        {
          "name": "systemProgram",
          "address": "11111111111111111111111111111111"
        }
      ],
      "args": [
        {
          "name": "admin",
          "type": "pubkey"
        },
        {
          "name": "oracleValidator",
          "type": "pubkey"
        }
      ]
    },
    {
      "name": "initScoreGroup",
      "discriminator": [
        39,
        15,
        214,
        155,
        127,
        99,
        188,
        10
      ],
      "accounts": [
        {
          "name": "validator",
          "writable": true,
          "signer": true
        },
        {
          "name": "globalConfig",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  103,
                  108,
                  111,
                  98,
                  97,
                  108,
                  45,
                  99,
                  111,
                  110,
                  102,
                  105,
                  103
                ]
              }
            ]
          }
        },
        {
          "name": "scoreGroup",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  115,
                  99,
                  111,
                  114,
                  101,
                  45,
                  103,
                  114,
                  111,
                  117,
                  112
                ]
              },
              {
                "kind": "arg",
                "path": "matchId"
              }
            ]
          }
        },
        {
          "name": "systemProgram",
          "address": "11111111111111111111111111111111"
        }
      ],
      "args": [
        {
          "name": "matchId",
          "type": "u64"
        },
        {
          "name": "firstScore",
          "type": "u8"
        },
        {
          "name": "startTimestamp",
          "type": "u64"
        }
      ]
    },
    {
      "name": "updateScoreGroup",
      "discriminator": [
        69,
        118,
        126,
        70,
        174,
        56,
        115,
        249
      ],
      "accounts": [
        {
          "name": "validator",
          "writable": true,
          "signer": true
        },
        {
          "name": "globalConfig",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  103,
                  108,
                  111,
                  98,
                  97,
                  108,
                  45,
                  99,
                  111,
                  110,
                  102,
                  105,
                  103
                ]
              }
            ]
          }
        },
        {
          "name": "scoreGroup",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  115,
                  99,
                  111,
                  114,
                  101,
                  45,
                  103,
                  114,
                  111,
                  117,
                  112
                ]
              },
              {
                "kind": "arg",
                "path": "matchId"
              }
            ]
          }
        }
      ],
      "args": [
        {
          "name": "matchId",
          "type": "u64"
        },
        {
          "name": "scores",
          "type": "bytes"
        },
        {
          "name": "timestamp",
          "type": {
            "vec": "u64"
          }
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "globalConfig",
      "discriminator": [
        149,
        8,
        156,
        202,
        160,
        252,
        176,
        217
      ]
    },
    {
      "name": "scoreGroup",
      "discriminator": [
        35,
        227,
        44,
        213,
        184,
        40,
        112,
        178
      ]
    }
  ],
  "errors": [
    {
      "code": 6000,
      "name": "invalidTimestamp",
      "msg": "Timestamp is invalid"
    },
    {
      "code": 6001,
      "name": "invalidInput",
      "msg": "Invalid Input"
    },
    {
      "code": 6002,
      "name": "matchEnded",
      "msg": "Match has ended"
    },
    {
      "code": 6003,
      "name": "notAuthorizedValidator",
      "msg": "Not authorized validator"
    },
    {
      "code": 6004,
      "name": "matchIsInProgress",
      "msg": "Match is in progress"
    }
  ],
  "types": [
    {
      "name": "globalConfig",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "admin",
            "type": "pubkey"
          },
          {
            "name": "oracleValidator",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "scoreGroup",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "scoreGroup",
            "type": {
              "array": [
                "u8",
                9000
              ]
            }
          },
          {
            "name": "matchId",
            "type": "u64"
          },
          {
            "name": "startTimestamp",
            "type": "u64"
          },
          {
            "name": "currentIndex",
            "type": "u64"
          },
          {
            "name": "lastUpdate",
            "type": "u64"
          },
          {
            "name": "isEnded",
            "type": "u8"
          },
          {
            "name": "padding",
            "type": {
              "array": [
                "u8",
                7
              ]
            }
          }
        ]
      }
    }
  ]
};
