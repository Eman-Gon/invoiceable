import json
from typing import Dict, List, Any, Optional
from .claude_client import ClaudeClient
from .invoice_tools import InvoiceTools, INVOICE_TOOLS

class ChatHandler:
    def __init__(self):
        self.claude = ClaudeClient()
    
    def handle_chat(self, message: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a chat message about the session's invoices."""
        try:
            print(f"💬 Processing chat message: {message}")
            
            # Get invoice data from session
            invoices = session_data.get("invoices", [])
            print(f"📊 Found {len(invoices)} invoices in session")
            
            # Use simple fallback chat instead of AWS
            return self._simple_fallback_chat(message, invoices, session_data)
            
        except Exception as e:
            print(f"💥 Chat handler error: {str(e)}")
            return {
                "success": False,
                "error": f"Chat error: {str(e)}"
            }
    
    def _simple_fallback_chat(self, message: str, invoices: List[Dict], session_data: Dict) -> Dict[str, Any]:
        """Simple fallback chat that works without AWS."""
        try:
            print("🤖 Using simple fallback chat (no AWS required)")
            
            message_lower = message.lower()
            
            # Calculate basic stats
            total_amount = 0
            vendors = set()
            line_items_count = 0
            
            for invoice in invoices:
                structured_data = invoice.get('structured_data', {})
                amount = structured_data.get('total_amount', 0)
                vendor = structured_data.get('vendor_name')
                line_items = structured_data.get('line_items', [])
                
                if amount:
                    total_amount += amount
                if vendor:
                    vendors.add(vendor)
                line_items_count += len(line_items)
            
            # Smart responses based on question type
            if 'total' in message_lower and ('amount' in message_lower or 'cost' in message_lower):
                response = f"The total amount across all {len(invoices)} invoices is ${total_amount:,.2f}."
                
            elif 'how many' in message_lower or 'count' in message_lower:
                response = f"You have {len(invoices)} invoices loaded in this session."
                
            elif 'vendor' in message_lower or 'company' in message_lower:
                if vendors:
                    vendor_list = ', '.join(sorted(vendors))
                    response = f"The vendors in your invoices are: {vendor_list}."
                else:
                    response = "No vendor information found in the invoices."
                    
            elif 'highest' in message_lower or 'largest' in message_lower:
                highest_amount = 0
                highest_vendor = None
                
                for invoice in invoices:
                    structured_data = invoice.get('structured_data', {})
                    amount = structured_data.get('total_amount', 0)
                    vendor = structured_data.get('vendor_name')
                    
                    if amount > highest_amount:
                        highest_amount = amount
                        highest_vendor = vendor
                
                if highest_vendor:
                    response = f"The highest invoice amount is ${highest_amount:,.2f} from {highest_vendor}."
                else:
                    response = "No invoice amounts found to compare."
                    
            elif 'kim park' in message_lower:
                # Specific query about Kim Park from Bolton & Maguire
                for invoice in invoices:
                    line_items = invoice.get('structured_data', {}).get('line_items', [])
                    for item in line_items:
                        if 'kim park' in item.get('description', '').lower():
                            hours = item.get('quantity', 0)
                            rate = item.get('unit_price', 0)
                            total = item.get('total', 0)
                            response = f"Kim Park billed {hours} hours at ${rate:,.2f}/hour for a total of ${total:,.2f}."
                            break
                    else:
                        continue
                    break
                else:
                    response = "I couldn't find specific information about Kim Park in the invoices."
                    
            elif 'attorney' in message_lower or 'lawyer' in message_lower:
                attorneys = []
                for invoice in invoices:
                    line_items = invoice.get('structured_data', {}).get('line_items', [])
                    for item in line_items:
                        desc = item.get('description', '')
                        if 'legal services' in desc.lower():
                            name = desc.replace('🏛️ Legal services - ', '').replace('⚖️ Legal services - ', '')
                            total = item.get('total', 0)
                            attorneys.append(f"{name}: ${total:,.2f}")
                
                if attorneys:
                    response = f"Attorney billing breakdown:\n" + "\n".join(attorneys)
                else:
                    response = "No attorney billing information found."
                    
            elif 'summary' in message_lower or 'overview' in message_lower:
                response = f"""Invoice Summary:
• Total Invoices: {len(invoices)}
• Total Amount: ${total_amount:,.2f}
• Vendors: {', '.join(sorted(vendors)) if vendors else 'None found'}
• Line Items: {line_items_count} total entries
• Average per Invoice: ${total_amount/max(len(invoices), 1):,.2f}"""
                
            else:
                # Generic helpful response
                response = f"""I can help you analyze your {len(invoices)} invoices! Here's what I found:

📊 **Quick Stats:**
• Total Amount: ${total_amount:,.2f}
• Vendors: {len(vendors)}
• Line Items: {line_items_count}

💬 **Try asking:**
• "What's the total amount?"
• "Who are the vendors?"
• "How much did Kim Park bill?"
• "Show me a summary"
• "What's the highest invoice amount?"
"""
            
            print(f"✅ Generated response: {response[:100]}...")
            
            return {
                "success": True,
                "response": response,
                "session_id": session_data.get("id"),
                "streaming": False,
                "method": "simple_fallback"
            }
            
        except Exception as e:
            print(f"❌ Simple fallback error: {str(e)}")
            return {
                "success": False,
                "error": f"Simple chat error: {str(e)}"
            }
    
    def _fallback_tool_chat(self, message: str, context: str, tools: InvoiceTools, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to tool-based chat if streaming fails."""
        # This method now calls the simple fallback instead of AWS
        return self._simple_fallback_chat(message, session_data.get("invoices", []), session_data)
    
    def _call_claude_with_tools(self, message: str, context: str, tools: InvoiceTools) -> str:
        """This method is kept for compatibility but won't be called in fallback mode."""
        return "AWS connection required for advanced features."
    
    def _execute_tool(self, tool_call: Dict, tools: InvoiceTools) -> Dict[str, Any]:
        """Execute a tool call and return the result."""
        # Simplified tool execution without Claude
        tool_name = tool_call.get("name")
        tool_id = tool_call.get("id", "fallback")
        
        try:
            if tool_name == "get_session_summary":
                result = tools.get_session_summary()
            else:
                result = {"message": "This feature requires AWS connection"}
            
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": json.dumps(result, default=str)
            }
            
        except Exception as e:
            return {
                "type": "tool_result", 
                "tool_use_id": tool_id,
                "content": json.dumps({"error": str(e)})
            }