"""
Demo of Sohay's enhanced autonomous agent capabilities
"""

import os
import sys
import time
import asyncio
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Sohay modules
try:
    from sohay_agent import SohayAgent, Task
    from sohay_runner import SohayAssistant, TextColors
except ImportError:
    print("Error: Could not import Sohay modules.")
    print("Make sure sohay_agent.py and sohay_runner.py are in the current directory.")
    sys.exit(1)

async def demo_enhanced_agent():
    """Demonstrate the enhanced autonomous agent capabilities"""
    print("\n" + "="*70)
    print("Sohay Enhanced Autonomous Agent Demo")
    print("="*70 + "\n")
    
    print("This demo will showcase Sohay's enhanced autonomous agent capabilities:")
    print("1. Free web search (no API key required)")
    print("2. Enhanced planning with context awareness")
    print("3. Task dependencies")
    print("4. Long-term memory")
    print("5. Task scheduling\n")
    
    # Create Sohay instance and agent
    print("Initializing Sohay and creating autonomous agent...")
    sohay = SohayAssistant()
    agent = SohayAgent(sohay)
    agent.enable_autonomous_mode()
    
    # Clear any existing tasks
    for task in list(agent.tasks):
        agent.delete_task(task.id)
    
    # Step 1: Demonstrate free web search
    print("\n" + "-"*70)
    print("STEP 1: FREE WEB SEARCH")
    print("-"*70)
    
    print("Testing free web search functionality...")
    search_result = await agent.gather_information("quantum computing recent breakthroughs")
    print("\nSearch Results Preview:")
    print("-" * 40)
    # Truncate if too long
    preview = search_result[:500] + "... [truncated]" if len(search_result) > 500 else search_result
    print(preview)
    print("-" * 40)
    
    # Step 2: Demonstrate enhanced planning
    print("\n" + "-"*70)
    print("STEP 2: ENHANCED PLANNING WITH CONTEXT AWARENESS")
    print("-"*70)
    
    # Create a research task
    print("Creating a research task...")
    task1_result = agent.add_task(
        "Research the latest developments in quantum computing and summarize key breakthroughs", 
        priority=3
    )
    print(f"Task created: {task1_result}")
    
    # Activate the task
    task1 = agent.tasks[0]
    agent.activate_task(task1.id)
    print(f"Activated task: {task1.goal}")
    
    # Generate a plan
    print("\nGenerating enhanced plan...")
    await agent.plan_task()
    
    print("\nGenerated plan with context awareness:")
    for i, step in enumerate(task1.plan):
        print(f"  Step {i+1}: {step}")
    
    # Step 3: Demonstrate task dependencies
    print("\n" + "-"*70)
    print("STEP 3: TASK DEPENDENCIES")
    print("-"*70)
    
    # Create dependent tasks
    print("Creating tasks with dependencies...")
    
    # Task 2: Analysis task that depends on Task 1
    task2_result = agent.add_task(
        "Analyze the implications of quantum computing breakthroughs for cryptography",
        priority=2,
        depends_on=[task1.id]  # Depends on the research task
    )
    print(f"Task 2: {task2_result}")
    
    # Task 3: Report task that depends on Task 2
    task3_result = agent.add_task(
        "Write a report on quantum-resistant encryption methods",
        priority=4,
        depends_on=[agent.tasks[1].id]  # Depends on the analysis task
    )
    print(f"Task 3: {task3_result}")
    
    # Show task list with dependencies
    print("\nTask list with dependencies:")
    tasks_list = agent.list_tasks()
    print(tasks_list)
    
    # Step 4: Demonstrate long-term memory
    print("\n" + "-"*70)
    print("STEP 4: LONG-TERM MEMORY")
    print("-"*70)
    
    # Add some memories
    print("Adding insights to agent's memory...")
    agent.add_to_memory("Quantum Computing", "Quantum computers use qubits instead of classical bits")
    agent.add_to_memory("Quantum Computing", "Shor's algorithm can break RSA encryption")
    agent.add_to_memory("Cryptography", "Post-quantum cryptography is resistant to quantum attacks")
    agent.add_to_memory("Research Methods", "Always verify information from multiple sources")
    
    # Show memory status
    print("\nMemory status:")
    memory_status = agent.get_memory_summary()
    print(memory_status)
    
    # Recall relevant memories
    print("\nRecalling memories related to 'quantum':")
    quantum_memories = agent.get_relevant_memories("quantum")
    for i, memory in enumerate(quantum_memories):
        print(f"  Memory {i+1}: {memory}")
    
    # Step 5: Demonstrate scheduling
    print("\n" + "-"*70)
    print("STEP 5: TASK SCHEDULING")
    print("-"*70)
    
    # Create scheduled tasks
    print("Creating scheduled tasks...")
    
    # Daily task
    daily_task = agent.add_task(
        "Check for new quantum computing research papers",
        priority=2,
        schedule={"type": "daily", "interval": 1}
    )
    print(f"Daily task: {daily_task}")
    
    # Weekly task
    weekly_task = agent.add_task(
        "Summarize weekly developments in quantum computing",
        priority=3,
        schedule={"type": "weekly", "interval": 1}
    )
    print(f"Weekly task: {weekly_task}")
    
    # Schedule an existing task
    print("\nScheduling an existing task...")
    schedule_result = agent.handle_command("schedule task 1 monthly:1")
    print(f"Result: {schedule_result}")
    
    # Show scheduled tasks
    print("\nList of scheduled tasks:")
    scheduled_tasks = agent.handle_command("list scheduled")
    print(scheduled_tasks)
    
    # Show agent status with all enhancements
    print("\n" + "-"*70)
    print("FINAL AGENT STATUS")
    print("-"*70)
    
    status = agent.get_status()
    print(status)
    
    print("\n" + "="*70)
    print("Enhanced Autonomous Agent Demo Completed")
    print("="*70)
    print("\nSohay has been successfully enhanced with:")
    print("✓ Free web search capabilities")
    print("✓ Enhanced planning with context awareness")
    print("✓ Task dependencies")
    print("✓ Long-term memory")
    print("✓ Task scheduling")
    print("\nYou can now use these features in your Sohay assistant!")

if __name__ == "__main__":
    # Run the async demo
    asyncio.run(demo_enhanced_agent()) 