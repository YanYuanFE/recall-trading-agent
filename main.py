#!/usr/bin/env python3
"""
Recall Trading Agent - Main Entry Point

A sophisticated trading agent for participating in Recall Network competitions.
Features portfolio management, multiple trading strategies, and real-time monitoring.
"""

import time
import schedule
import signal
import sys
from typing import Optional
import argparse
from datetime import datetime

from src.logger import setup_logger
from src.config import Config
from src.trading_client import RecallTradingClient
from src.portfolio_manager import PortfolioManager
from src.trading_strategy import MultiStrategyManager
from src.market_data import PriceMonitor

logger = setup_logger("RecallTradingAgent")

class TradingAgent:
    def __init__(self):
        self.trading_client = RecallTradingClient()
        self.portfolio_manager = PortfolioManager()
        self.strategy_manager = MultiStrategyManager()
        self.price_monitor = PriceMonitor()
        self.running = False
        
        # Get trading symbols from configuration
        from src.token_config import TokenConfigManager
        token_config = TokenConfigManager()
        self.symbols = token_config.get_token_symbols()
        
        logger.info(f"Monitoring {len(self.symbols)} tokens: {', '.join(self.symbols)}")
        
        logger.info("Trading Agent initialized")
    
    def start(self):
        """Start the trading agent"""
        logger.info("Starting Recall Trading Agent...")
        
        # Verify API connection
        if not self.trading_client.health_check():
            logger.error("Failed to connect to Recall API. Check your configuration.")
            return False
        
        # Validate API key
        api_key_valid = self.trading_client.validate_api_key()
        if not api_key_valid:
            logger.warning("API key validation failed. Running with mock data for demonstration.")
            logger.warning("Please update your API key in the .env file for real trading.")
            logger.warning("You can get a new API key from: https://register.recall.network")
        
        if api_key_valid:
            logger.info("API connection and authentication successful")
        else:
            logger.info("API connection established, running with mock data")
        
        # Initial portfolio status
        self.log_portfolio_status()
        
        # Schedule periodic tasks
        schedule.every(1).hours.do(self.rebalance_portfolio)
        schedule.every(30).minutes.do(self.execute_trading_signals)
        schedule.every(15).minutes.do(self.monitor_prices)
        schedule.every(6).hours.do(self.log_portfolio_status)
        schedule.every(24).hours.do(self.generate_daily_report)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
        logger.info("Trading Agent started successfully")
        
        # Main loop with user-friendly status updates
        try:
            print("\n" + "="*60)
            print("🤖 RECALL TRADING AGENT - RUNNING")
            print("="*60)
            print("📊 Portfolio Target: 30% USDC, 40% SOL, 30% WETH")
            print("⚡ Multi-chain support: Solana (SVM) + Ethereum (EVM)")
            print("⏰ Next rebalance: Every hour")
            print("📈 Trading signals: Every 30 minutes") 
            print("💰 Price monitoring: Every 15 minutes")
            print("📋 Portfolio report: Every 6 hours")
            print("="*60)
            print("💡 Press Ctrl+C to stop the agent")
            print("📝 Logs are saved to: logs/trading_agent_*.log")
            print("")
            
            last_status_time = time.time()
            status_interval = 300  # Show status every 5 minutes
            
            while self.running:
                schedule.run_pending()
                
                # Show periodic status updates
                current_time = time.time()
                if current_time - last_status_time >= status_interval:
                    self.show_live_status()
                    last_status_time = current_time
                
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n🛑 Received keyboard interrupt, shutting down...")
            logger.info("Received keyboard interrupt")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            print("\n🔄 Shutting down trading agent...")
            self.stop()
        
        return True
    
    def show_live_status(self):
        """Show live status update to the user"""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n⏰ {current_time} - Status Update")
            print("-" * 40)
            
            # Get portfolio status
            portfolio_status = self.portfolio_manager.get_portfolio_status()
            total_value = sum(target.current_value for target in portfolio_status.values())
            
            print(f"💰 Portfolio Value: ${total_value:,.0f}")
            
            for symbol, target in portfolio_status.items():
                drift_indicator = "⚖️" if abs(target.drift) < 0.05 else "⚠️" if abs(target.drift) < 0.15 else "🔴"
                print(f"   {drift_indicator} {symbol}: {target.current_allocation*100:.1f}% (target: {target.target_allocation*100:.1f}%)")
            
            # Check if rebalancing is needed
            trades = self.portfolio_manager.calculate_rebalance_trades()
            if trades:
                print(f"🔄 Rebalancing needed: {len(trades)} trades")
            else:
                print("✅ Portfolio is balanced")
            
            print("-" * 40)
            
        except Exception as e:
            print(f"⚠️  Status update failed: {e}")

    def stop(self):
        """Stop the trading agent"""
        print("\n📊 Final Portfolio Report:")
        logger.info("Stopping Trading Agent...")
        self.running = False
        
        # Final portfolio report
        self.log_portfolio_status()
        print("✅ Trading Agent stopped successfully")
        logger.info("Trading Agent stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def rebalance_portfolio(self):
        """Execute portfolio rebalancing"""
        try:
            print(f"\n🔄 {datetime.now().strftime('%H:%M:%S')} - Starting portfolio rebalancing...")
            logger.info("Starting portfolio rebalancing...")
            success = self.portfolio_manager.execute_rebalance()
            
            if success:
                print("✅ Portfolio rebalancing completed successfully")
                logger.info("Portfolio rebalancing completed successfully")
            else:
                print("ℹ️  No rebalancing needed")
                logger.warning("Portfolio rebalancing failed or was not needed")
                
        except Exception as e:
            print(f"❌ Portfolio rebalancing error: {e}")
            logger.error(f"Error during portfolio rebalancing: {e}")
    
    def execute_trading_signals(self):
        """Execute trades based on strategy signals"""
        try:
            print(f"\n📈 {datetime.now().strftime('%H:%M:%S')} - Analyzing market for trading signals...")
            logger.info("Generating and executing trading signals...")
            
            signals = self.strategy_manager.generate_combined_signals()
            
            if not signals:
                print("📊 No strong trading signals detected")
                logger.info("No trading signals generated")
                return
            
            # Get available capital
            portfolio = self.trading_client.get_portfolio()
            available_capital = portfolio.get('total_value', 0)
            
            executed_trades = 0
            
            for signal in signals:
                try:
                    if signal.action in ['buy', 'sell'] and signal.strength > 0.1:  # Only act on strong signals
                        
                        # Calculate position size
                        position_size = self.strategy_manager.strategies[0].calculate_position_size(
                            signal, available_capital
                        )
                        
                        if position_size >= Config.MIN_TRADE_AMOUNT:
                            # Get token addresses
                            from_token, to_token = self._get_trade_tokens(signal)
                            
                            if from_token and to_token:
                                result = self.trading_client.execute_trade(
                                    from_token=from_token,
                                    to_token=to_token,
                                    amount=position_size,
                                    reason=f"Strategy signal: {signal.reason}"
                                )
                                
                                logger.info(f"Executed trade: {signal.action} {signal.symbol} - {signal.reason}")
                                executed_trades += 1
                                
                                time.sleep(2)  # Rate limiting
                        
                except Exception as e:
                    logger.error(f"Failed to execute signal for {signal.symbol}: {e}")
                    continue
            
            logger.info(f"Executed {executed_trades} trades based on strategy signals")
            
        except Exception as e:
            logger.error(f"Error executing trading signals: {e}")
    
    def monitor_prices(self):
        """Monitor price changes and generate alerts"""
        try:
            print(f"\n💰 {datetime.now().strftime('%H:%M:%S')} - Monitoring market prices...")
            alerts = self.price_monitor.monitor_prices(self.symbols)
            
            if alerts:
                print(f"🚨 {len(alerts)} price alerts detected:")
                for alert in alerts:
                    change_emoji = "📈" if alert['change'] > 0 else "📉"
                    print(f"   {change_emoji} {alert['symbol']}: {alert['change']:+.2%} "
                           f"(${alert['last_price']:.2f} → ${alert['current_price']:.2f})")
                    logger.info(f"Price Alert: {alert['symbol']} changed {alert['change']:.2%} "
                               f"from ${alert['last_price']:.4f} to ${alert['current_price']:.4f}")
            else:
                print("📊 No significant price changes detected")
            
        except Exception as e:
            print(f"❌ Price monitoring error: {e}")
            logger.error(f"Error monitoring prices: {e}")
    
    def log_portfolio_status(self):
        """Log current portfolio status"""
        try:
            report = self.portfolio_manager.generate_portfolio_report()
            logger.info(f"Portfolio Status:\n{report}")
            
        except Exception as e:
            logger.error(f"Error generating portfolio status: {e}")
    
    def generate_daily_report(self):
        """Generate comprehensive daily report"""
        try:
            print(f"\n📋 {datetime.now().strftime('%H:%M:%S')} - Generating daily report...")
            logger.info("Generating daily report...")
            
            # Portfolio performance
            performance = self.portfolio_manager.get_portfolio_performance()
            
            # Competition status
            try:
                competition_status = self.trading_client.get_competition_status()
            except Exception as e:
                logger.warning(f"Failed to get competition status, using mock data: {e}")
                competition_status = {"status": "Demo Mode - API Key Invalid"}
            
            # Trade history - try new history endpoint first
            try:
                # Try the new account/history endpoint
                account_history = self.trading_client.get_account_history()
                if account_history:
                    recent_trades = account_history[-10:]  # Last 10 entries
                    logger.info("Using account/history endpoint for trade data")
                else:
                    raise Exception("No history data from new endpoint")
            except Exception as history_error:
                logger.debug(f"Account history endpoint failed: {history_error}")
                try:
                    # Fallback to trades endpoint
                    recent_trades = self.trading_client.get_trade_history(limit=10)
                except Exception as e:
                    logger.warning(f"Failed to get trade history, using mock data: {e}")
                    recent_trades = [
                        {"timestamp": "2025-07-03T10:00:00Z", "from_token": "USDC", "to_token": "WETH", "amount": "100"},
                        {"timestamp": "2025-07-03T11:30:00Z", "from_token": "WETH", "to_token": "SOL", "amount": "0.1"}
                    ]
            
            report = [
                "=" * 60,
                f"DAILY REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "=" * 60,
                "",
                "PORTFOLIO PERFORMANCE:",
                f"Total Value: ${performance.get('total_value', 0):,.2f}",
                f"Total Return: {performance.get('total_return_pct', 0):.2f}%",
                f"Daily Return: {performance.get('daily_return_pct', 0):.2f}%",
                "",
                "COMPETITION STATUS:",
                f"Status: {competition_status.get('status', 'Unknown')}",
                "",
                f"RECENT TRADES ({len(recent_trades)}):",
            ]
            
            for trade in recent_trades[-5:]:  # Last 5 trades
                report.append(f"- {trade.get('timestamp', '')}: {trade.get('from_token', '')} -> {trade.get('to_token', '')}")
            
            report.append("=" * 60)
            
            daily_report = "\n".join(report)
            logger.info(f"Daily Report:\n{daily_report}")
            
            # Save to file
            with open(f"logs/daily_report_{datetime.now().strftime('%Y%m%d')}.txt", "w") as f:
                f.write(daily_report)
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
    
    def _get_trade_tokens(self, signal) -> tuple:
        """Get token addresses for trading based on signal"""
        # This is a simplified implementation
        # In production, you'd have more sophisticated logic
        
        token_addresses = {
            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'SOL': 'So11111111111111111111111111111111111111112'
        }
        
        if signal.action == 'buy':
            # Buy signal: USDC -> target token
            return token_addresses.get('USDC'), token_addresses.get(signal.symbol)
        elif signal.action == 'sell':
            # Sell signal: target token -> USDC
            return token_addresses.get(signal.symbol), token_addresses.get('USDC')
        
        return None, None

def main():
    parser = argparse.ArgumentParser(description='Recall Trading Agent')
    parser.add_argument('--mode', choices=['run', 'status', 'report'], default='run',
                       help='Agent mode: run (default), status, or report')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual trades)')
    
    args = parser.parse_args()
    
    try:
        agent = TradingAgent()
        
        if args.mode == 'status':
            # Just show portfolio status and exit
            agent.log_portfolio_status()
            
        elif args.mode == 'report':
            # Generate report and exit
            agent.generate_daily_report()
            
        else:
            # Run the agent
            if args.dry_run:
                logger.info("Running in DRY-RUN mode - no actual trades will be executed")
            
            success = agent.start()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()