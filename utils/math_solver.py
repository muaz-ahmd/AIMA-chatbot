import re
import ast
import operator
from typing import Optional, Tuple

class MathSolver:
    """Safe math expression evaluator for basic arithmetic."""
    
    # Supported operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }
    
    def __init__(self):
        # Regex to detect math expressions
        # Matches: numbers, +, -, *, /, ^, %, (, ), spaces
        self.math_pattern = re.compile(
            r'^[\d\s\+\-\*/\(\)\^\%\.]+$'
        )
    
    def is_math_expression(self, text: str) -> bool:
        """Check if text looks like a math expression."""
        # Clean up
        cleaned = text.strip()
        
        # Replace common math symbols
        cleaned = cleaned.replace('^', '**')  # Power
        cleaned = cleaned.replace('x', '*')   # Multiplication (optional)
        cleaned = cleaned.replace('×', '*')   # Multiplication symbol
        cleaned = cleaned.replace('÷', '/')   # Division symbol
        
        # Check if it matches math pattern
        if not self.math_pattern.match(cleaned):
            return False
        
        # Additional validation: must have at least one number and one operator
        has_number = bool(re.search(r'\d', cleaned))
        has_operator = bool(re.search(r'[\+\-\*/\%]', cleaned))
        
        return has_number and has_operator
    
    def solve(self, expression: str) -> Optional[Tuple[float, str]]:
        """
        Safely evaluate a math expression.
        Returns (result, formatted_string) or None if invalid.
        """
        try:
            # Clean and normalize
            cleaned = expression.strip()
            cleaned = cleaned.replace('^', '**')
            cleaned = cleaned.replace('x', '*')
            cleaned = cleaned.replace('×', '*')
            cleaned = cleaned.replace('÷', '/')
            
            # Parse using AST (safe - no code execution)
            tree = ast.parse(cleaned, mode='eval')
            
            # Evaluate the expression tree
            result = self._eval_node(tree.body)
            
            # Format result
            if isinstance(result, float):
                # Show up to 6 decimal places, strip trailing zeros
                formatted = f"{result:.6f}".rstrip('0').rstrip('.')
            else:
                formatted = str(result)
            
            return result, formatted
            
        except (SyntaxError, ValueError, TypeError, KeyError, ZeroDivisionError) as e:
            # Invalid expression
            return None
    
    def _eval_node(self, node):
        """Recursively evaluate AST node."""
        if isinstance(node, ast.Num):  # Number
            return node.n
        
        elif isinstance(node, ast.BinOp):  # Binary operation
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.OPERATORS.get(type(node.op))
            
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            
            return op(left, right)
        
        elif isinstance(node, ast.UnaryOp):  # Unary operation (e.g., -5)
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        
        else:
            raise ValueError(f"Unsupported expression type: {type(node)}")
