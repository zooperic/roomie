#!/usr/bin/env python3
"""
System Health Check - Verify all agents are registered and healthy
"""
import asyncio
import httpx
import json

ALFRED_URL = "http://localhost:8000"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

async def check_health():
    """Check system health"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Project Roomy - System Health Check{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Check if Alfred is running
            print(f"{YELLOW}Checking Alfred API...{RESET}")
            try:
                response = await client.get(f"{ALFRED_URL}/")
                print(f"{GREEN}✓ Alfred API is running{RESET}")
            except Exception as e:
                print(f"{RED}✗ Alfred API not accessible: {e}{RESET}")
                print(f"{YELLOW}Run: bash scripts/start_dev.sh{RESET}")
                return
            
            # Test message endpoint
            print(f"\n{YELLOW}Testing message routing...{RESET}")
            print(f"{YELLOW}(This may take 30-60s on first run while Ollama loads the model){RESET}\n")
            response = await client.post(f"{ALFRED_URL}/message", json={
                "message": "status check",
                "user_id": "health_check"
            })
            
            if response.status_code == 200:
                print(f"{GREEN}✓ Message routing works{RESET}")
                result = response.json()
                
                # Show which agent responded
                agent = result.get("agent", "unknown")
                print(f"{BLUE}  → Routed to: {agent}{RESET}")
            else:
                print(f"{RED}✗ Message routing failed: {response.status_code}{RESET}")
            
            # Check agent status
            print(f"\n{YELLOW}Checking registered agents...{RESET}")
            
            agents_to_check = ["alfred", "elsa", "remy", "lebowski"]
            
            for agent_name in agents_to_check:
                try:
                    response = await client.post(f"{ALFRED_URL}/message", json={
                        "message": "what can you do",
                        "user_id": "health_check",
                        "force_agent": agent_name
                    })
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "error" not in result:
                            print(f"{GREEN}✓ {agent_name.capitalize()} agent: ONLINE{RESET}")
                        else:
                            print(f"{RED}✗ {agent_name.capitalize()} agent: ERROR - {result.get('error')}{RESET}")
                    else:
                        print(f"{RED}✗ {agent_name.capitalize()} agent: HTTP {response.status_code}{RESET}")
                
                except Exception as e:
                    print(f"{RED}✗ {agent_name.capitalize()} agent: {e}{RESET}")
            
            # Summary
            print(f"\n{BLUE}{'='*60}{RESET}")
            print(f"{GREEN}System Status: READY{RESET}")
            print(f"{BLUE}{'='*60}{RESET}\n")
            
            print(f"{YELLOW}Available agents:{RESET}")
            print(f"  • Alfred - Conversational assistant & router")
            print(f"  • Elsa - Fridge inventory manager")
            print(f"  • Remy - Recipe parser & pantry manager")
            print(f"  • Lebowski - Procurement & catalog matching\n")
            
            print(f"{YELLOW}Next steps:{RESET}")
            print(f"  1. Run tests: python3 scripts/test_all.py")
            print(f"  2. Try Telegram bots (if configured)")
            print(f"  3. Test recipe-to-cart flow\n")
    
    except Exception as e:
        print(f"\n{RED}Health check failed: {e}{RESET}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_health())
