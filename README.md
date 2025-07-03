# Recall Trading Agent

A sophisticated AI trading agent designed for participating in Recall Network competitions. This agent features automated portfolio management, multiple trading strategies, and real-time market monitoring.

## Features

- **Multi-Strategy Trading**: Implements momentum and mean reversion strategies
- **Portfolio Management**: Automated rebalancing based on target allocations
- **Real-time Monitoring**: Price alerts and market data tracking
- **Risk Management**: Position sizing and stop-loss mechanisms
- **Competition Integration**: Built specifically for Recall Network competitions
- **Comprehensive Logging**: Detailed logging and daily reports

## Project Structure

```
recall-trading-agent/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── trading_client.py      # Recall API client
│   ├── portfolio_manager.py   # Portfolio management logic
│   ├── trading_strategy.py    # Trading strategies
│   ├── market_data.py         # Market data and price monitoring
│   └── logger.py              # Logging setup
├── config/
│   └── portfolio_config.json  # Portfolio configuration
├── logs/                      # Log files
├── tests/                     # Test files
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Quick Start

### 1. Installation

```bash
# Clone or create the project directory
cd recall-trading-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
TRADING_SIM_API_KEY=your_api_key_here
TRADING_SIM_API_URL=https://api.competitions.recall.network
```

### 3. Register for Recall Competition

1. Visit https://register.recall.network
2. Create your account and team
3. Get your API key
4. Update the `.env` file with your credentials

### 4. Run the Agent

```bash
# Run the trading agent
python main.py

# Check portfolio status only
python main.py --mode status

# Generate daily report
python main.py --mode report

# Run in dry-run mode (no actual trades)
python main.py --dry-run
```

## Configuration

### Portfolio Configuration (`config/portfolio_config.json`)

```json
{
  "target_allocations": {
    "USDC": 0.3,
    "WETH": 0.4,
    "SOL": 0.3
  },
  "rebalance_threshold": 0.05,
  "min_trade_amount": 10,
  "max_slippage": 0.01
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TRADING_SIM_API_KEY` | Recall API key | Required |
| `TRADING_SIM_API_URL` | Recall API URL | https://api.competitions.recall.network |
| `PORTFOLIO_REBALANCE_INTERVAL` | Rebalance interval (seconds) | 3600 |
| `MAX_SLIPPAGE` | Maximum slippage tolerance | 0.01 |
| `MIN_TRADE_AMOUNT` | Minimum trade amount (USDC) | 10 |
| `MAX_POSITION_SIZE` | Maximum position size (% of portfolio) | 0.3 |
| `STOP_LOSS_THRESHOLD` | Stop loss threshold | 0.05 |
| `LOG_LEVEL` | Logging level | INFO |

## Trading Strategies

### 1. Momentum Strategy
- Analyzes price momentum over configurable periods
- Generates buy signals for positive momentum
- Generates sell signals for negative momentum
- Configurable momentum threshold and lookback period

### 2. Mean Reversion Strategy
- Uses statistical analysis to identify overbought/oversold conditions
- Calculates Z-scores based on historical price data
- Generates contrarian signals when prices deviate significantly from mean
- Configurable Z-score threshold and lookback period

### 3. Multi-Strategy Combination
- Combines signals from multiple strategies
- Resolves conflicting signals using weighted approach
- Provides more robust trading decisions

## Portfolio Management

### Automated Rebalancing
- Monitors portfolio allocation vs. target weights
- Calculates required trades to maintain target allocation
- Executes rebalancing trades when drift exceeds threshold
- Considers minimum trade amounts and slippage

### Risk Management
- Position sizing based on signal strength
- Maximum position size limits
- Stop-loss mechanisms
- Slippage control

## Monitoring and Reporting

### Real-time Monitoring
- Price change alerts
- Portfolio performance tracking
- Trade execution monitoring
- API health checks

### Daily Reports
- Portfolio performance summary
- Recent trade history
- Competition status
- Detailed allocation analysis

## API Integration

The agent integrates with the Recall Network API for:
- Portfolio and balance queries
- Trade execution
- Price data retrieval
- Competition status
- Leaderboard information

### Supported Endpoints
- `/account/portfolio` - Portfolio information
- `/account/balances` - Token balances
- `/trade/execute` - Trade execution
- `/trade/quote` - Trade quotes
- `/price` - Token prices
- `/competition/status` - Competition status
- `/competition/leaderboard` - Leaderboard

## Security

- API keys are stored in environment variables
- No credentials are logged or committed to version control
- Secure error handling prevents credential exposure
- Rate limiting to prevent API abuse

## Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src
```

### Adding New Strategies
1. Create a new strategy class inheriting from `TradingStrategy`
2. Implement `generate_signals()` and `calculate_position_size()` methods
3. Add the strategy to `MultiStrategyManager`

### Extending Market Data
1. Add new data sources in `market_data.py`
2. Implement additional technical indicators
3. Enhance price monitoring capabilities

## Troubleshooting

### Common Issues
1. **API Connection Failed**: Check API key and network connectivity
2. **Insufficient Balance**: Ensure adequate test funds in sandbox
3. **Trade Execution Failed**: Check token addresses and slippage settings
4. **Rate Limiting**: Reduce trading frequency or add delays

### Logs
- Application logs: `logs/trading_agent_YYYYMMDD.log`
- Daily reports: `logs/daily_report_YYYYMMDD.txt`
- Error logs: Check console output and log files

## Competition Tips

1. **Test Thoroughly**: Use sandbox mode to test strategies
2. **Monitor Performance**: Track key metrics and adjust as needed
3. **Risk Management**: Don't risk more than you can afford to lose
4. **Diversification**: Spread risk across multiple tokens and strategies
5. **Stay Updated**: Monitor competition rules and market conditions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues:
- Check the logs for error messages
- Review the Recall Network documentation
- Join the Recall Discord community
- Open an issue on GitHub

## Disclaimer

This software is for educational and competition purposes only. Trading involves risk, and past performance does not guarantee future results. Use at your own risk.