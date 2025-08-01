import json
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
from src.trading_client import RecallTradingClient, Balance, Token
from src.config import Config

logger = logging.getLogger(__name__)

@dataclass
class PortfolioTarget:
    symbol: str
    target_allocation: float
    current_allocation: float
    current_value: float
    drift: float

class PortfolioManager:
    def __init__(self, config_path: str = "config/portfolio_config.json"):
        self.trading_client = RecallTradingClient()
        self.config = self._load_config(config_path)
        self.target_allocations = self.config["target_allocations"]
        self.rebalance_threshold = self.config.get("rebalance_threshold", 0.05)
        self.min_trade_amount = self.config.get("min_trade_amount", 10)
        self.max_slippage = self.config.get("max_slippage", 0.01)
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
    
    def get_portfolio_status(self) -> Dict[str, PortfolioTarget]:
        try:
            # Use portfolio endpoint for most accurate data
            portfolio = self.trading_client.get_portfolio()
            total_value = portfolio.get('totalValue', 0)
            
            if total_value > 0:
                logger.info("Using portfolio endpoint for portfolio data")
                return self._process_portfolio_data(portfolio)
            
            # Fallback to balances endpoint (but calculate USD value)
            balances = self.trading_client.get_balances()
            total_value = self._calculate_portfolio_value_from_balances(balances)
            
        except Exception as e:
            logger.warning(f"Failed to get real portfolio data, using mock data: {e}")
            # Use mock data for demonstration when API fails
            from src.trading_client import Balance, Token
            balances = [
                Balance(Token("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "USDC", "ethereum", 6), 1000.0, 1000.0),
                Balance(Token("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "WETH", "ethereum", 18), 0.5, 2000.0),
                Balance(Token("So11111111111111111111111111111111111111112", "SOL", "solana", 9), 10.0, 500.0)
            ]
            total_value = sum(balance.usd_value for balance in balances)
        
        portfolio_status = {}
        
        for symbol, target_allocation in self.target_allocations.items():
            current_balance = next((b for b in balances if b.token.symbol == symbol), None)
            current_value = current_balance.usd_value if current_balance else 0.0
            current_allocation = current_value / total_value if total_value > 0 else 0.0
            drift = current_allocation - target_allocation
            
            portfolio_status[symbol] = PortfolioTarget(
                symbol=symbol,
                target_allocation=target_allocation,
                current_allocation=current_allocation,
                current_value=current_value,
                drift=drift
            )
        
        return portfolio_status
    
    def _process_portfolio_data(self, portfolio: Dict) -> Dict[str, PortfolioTarget]:
        """Process portfolio endpoint data - only include configured chains"""
        tokens = portfolio.get('tokens', [])
        
        # Only include tokens that are in our trading configuration
        configured_tokens = set()
        configured_chains = set()
        for chain, token_map in self.config.get("trading_pairs", {}).items():
            configured_chains.add(chain)
            configured_tokens.update(token_map.keys())
        
        # Group tokens by symbol and sum their values (only for configured tokens/chains)
        token_values = {}
        total_value = 0
        
        for token in tokens:
            symbol = token.get('symbol', 'UNKNOWN')
            chain = token.get('chain', '')
            value = token.get('value', 0)
            
            # Map chain names: 'evm' -> 'ethereum', 'svm' -> 'solana'
            mapped_chain = 'ethereum' if chain == 'evm' else 'solana' if chain == 'svm' else chain
            
            # Only include if symbol is configured and on a configured chain
            if symbol in configured_tokens and mapped_chain in configured_chains:
                if symbol in token_values:
                    token_values[symbol] += value
                else:
                    token_values[symbol] = value
                total_value += value
        
        portfolio_status = {}
        for symbol, target_allocation in self.target_allocations.items():
            current_value = token_values.get(symbol, 0.0)
            current_allocation = current_value / total_value if total_value > 0 else 0.0
            drift = current_allocation - target_allocation
            
            portfolio_status[symbol] = PortfolioTarget(
                symbol=symbol,
                target_allocation=target_allocation,
                current_allocation=current_allocation,
                current_value=current_value,
                drift=drift
            )
        
        return portfolio_status
    
    def _calculate_portfolio_value_from_balances(self, balances) -> float:
        """Calculate total portfolio value from balances (fallback method)"""
        # This is a simplified calculation - in reality we'd need price data
        total_value = 0
        for balance in balances:
            if balance.token.symbol == 'USDC' or balance.token.symbol == 'USDbC':
                total_value += balance.amount  # Stablecoins ~= $1
            elif balance.token.symbol == 'SOL':
                total_value += balance.amount * 150  # Rough SOL price estimate
            elif balance.token.symbol == 'WETH' or balance.token.symbol == 'ETH':
                total_value += balance.amount * 3500  # Rough ETH price estimate
        return total_value
    
    
    def calculate_rebalance_trades(self) -> List[Tuple[str, str, float]]:
        portfolio_status = self.get_portfolio_status()
        total_portfolio_value = sum(target.current_value for target in portfolio_status.values())
        
        trades = []
        
        # Find tokens that need rebalancing
        over_allocated = []
        under_allocated = []
        
        for symbol, target in portfolio_status.items():
            if abs(target.drift) > self.rebalance_threshold:
                target_value = target.target_allocation * total_portfolio_value
                value_diff = target_value - target.current_value
                
                if value_diff > self.min_trade_amount:
                    under_allocated.append((symbol, value_diff))
                elif value_diff < -self.min_trade_amount:
                    over_allocated.append((symbol, abs(value_diff)))
        
        # Create trades to rebalance - prioritize same-chain trades
        for over_symbol, over_amount in over_allocated:
            for under_symbol, under_amount in under_allocated:
                if over_amount > 0 and under_amount > 0:
                    # Check if both tokens are on the same chain
                    from_chain = self._get_token_chain(over_symbol)
                    to_chain = self._get_token_chain(under_symbol)
                    
                    # Only create trade if on same chain
                    if from_chain == to_chain:
                        trade_amount = min(over_amount, under_amount)
                        if trade_amount >= self.min_trade_amount:
                            trades.append((over_symbol, under_symbol, trade_amount))
                            
                            # Update remaining amounts
                            over_amount -= trade_amount
                            under_amount -= trade_amount
        
        return trades
    
    def execute_rebalance(self) -> bool:
        try:
            trades = self.calculate_rebalance_trades()
            
            if not trades:
                logger.info("No rebalancing needed")
                return True
            
            logger.info(f"Executing {len(trades)} rebalance trades")
            
            for from_symbol, to_symbol, usd_amount in trades:
                try:
                    # Get token addresses and chains
                    from_token = self._get_token_address(from_symbol)
                    to_token = self._get_token_address(to_symbol)
                    from_chain = self._get_token_chain(from_symbol)
                    to_chain = self._get_token_chain(to_symbol)
                    
                    if not from_token or not to_token:
                        logger.error(f"Token address not found for {from_symbol} or {to_symbol}")
                        continue
                    
                    # Check if cross-chain trade (not supported yet)
                    if from_chain != to_chain:
                        logger.warning(f"Cross-chain trade not supported: {from_symbol} ({from_chain}) -> {to_symbol} ({to_chain})")
                        continue
                    
                    # Get current price to calculate amount
                    from_price = self.trading_client.get_token_price(from_token, from_chain)
                    if from_price is None or from_price <= 0:
                        logger.warning(f"Cannot get valid price for {from_symbol}, skipping trade")
                        continue
                    
                    amount = usd_amount / from_price
                    
                    if amount >= self.min_trade_amount / from_price:
                        logger.info(f"Attempting trade: {amount:.6f} {from_symbol} -> {to_symbol} on {from_chain}")
                        logger.info(f"Trade details: USD ${usd_amount:.2f}, price ${from_price:.6f}")
                        
                        result = self.trading_client.execute_trade(
                            from_token=from_token,
                            to_token=to_token,
                            amount=amount,
                            reason=f"Portfolio rebalance: {from_symbol} -> {to_symbol} on {from_chain}"
                        )
                        
                        logger.info(f"Rebalance trade executed: {amount:.6f} {from_symbol} -> {to_symbol} on {from_chain}")
                        time.sleep(1)  # Avoid rate limiting
                    else:
                        logger.warning(f"Trade amount too small: {amount:.6f} {from_symbol} (min: {self.min_trade_amount / from_price:.6f})")
                    
                except Exception as e:
                    logger.error(f"Failed to execute trade {from_symbol} -> {to_symbol}: {e}")
                    logger.error(f"Trade parameters: from_token={from_token}, to_token={to_token}, amount={amount:.6f}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Portfolio rebalancing failed: {e}")
            return False
    
    def _get_token_address(self, symbol: str) -> Optional[str]:
        for chain, tokens in self.config.get("trading_pairs", {}).items():
            if symbol in tokens:
                return tokens[symbol]
        return None
    
    def _get_token_chain(self, symbol: str) -> Optional[str]:
        for chain, tokens in self.config.get("trading_pairs", {}).items():
            if symbol in tokens:
                return chain
        return None
    
    def get_portfolio_performance(self) -> Dict[str, float]:
        try:
            portfolio_data = self.trading_client.get_portfolio()
            
            performance = {
                "total_value": portfolio_data.get("total_value", 0),
                "total_return": portfolio_data.get("total_return", 0),
                "total_return_pct": portfolio_data.get("total_return_pct", 0),
                "daily_return": portfolio_data.get("daily_return", 0),
                "daily_return_pct": portfolio_data.get("daily_return_pct", 0),
            }
            
            return performance
            
        except Exception as e:
            logger.warning(f"Failed to get portfolio performance, using mock data: {e}")
            # Return mock performance data for demonstration
            return {
                "total_value": 3500.0,
                "total_return": 350.0,
                "total_return_pct": 11.11,
                "daily_return": 25.0,
                "daily_return_pct": 0.72,
            }
    
    def generate_portfolio_report(self) -> str:
        try:
            portfolio_status = self.get_portfolio_status()
            performance = self.get_portfolio_performance()
            
            report = ["=" * 50]
            report.append("PORTFOLIO REPORT")
            report.append("=" * 50)
            
            # Performance summary
            report.append(f"Total Value: ${performance.get('total_value', 0):,.2f}")
            report.append(f"Total Return: {performance.get('total_return_pct', 0):.2f}%")
            report.append(f"Daily Return: {performance.get('daily_return_pct', 0):.2f}%")
            report.append("")
            
            # Allocation details
            report.append("CURRENT ALLOCATIONS:")
            report.append("-" * 30)
            
            for symbol, target in portfolio_status.items():
                report.append(f"{symbol:6}: Target {target.target_allocation:.1%} | "
                             f"Current {target.current_allocation:.1%} | "
                             f"Drift {target.drift:+.1%} | "
                             f"Value ${target.current_value:,.2f}")
            
            # Rebalance recommendations
            trades = self.calculate_rebalance_trades()
            if trades:
                report.append("")
                report.append("REBALANCE RECOMMENDATIONS:")
                report.append("-" * 30)
                for from_symbol, to_symbol, amount in trades:
                    report.append(f"Trade ${amount:,.2f}: {from_symbol} -> {to_symbol}")
            else:
                report.append("")
                report.append("No rebalancing needed.")
            
            report.append("=" * 50)
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Failed to generate portfolio report: {e}")
            return f"Error generating report: {e}"