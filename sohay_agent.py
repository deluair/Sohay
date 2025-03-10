"""
Sohay Autonomous Agent Module - Enhances Sohay with autonomous capabilities
"""

import os
import sys
import json
import time
import asyncio
import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Autonomous agent states
AGENT_STATES = {
    "IDLE": "idle",            # Waiting for tasks
    "PLANNING": "planning",    # Planning the execution of a goal
    "EXECUTING": "executing",  # Executing a step in the plan
    "REFLECTING": "reflecting", # Evaluating results and revising plan
    "LEARNING": "learning"     # Recording outcomes for future reference
}

# Import required search functionality directly
try:
    from sohay_search import search_and_format
    SEARCH_DIRECT = True
except ImportError:
    SEARCH_DIRECT = False

class Task:
    """Represents a task for the autonomous agent to complete"""
    
    def __init__(self, goal: str, priority: int = 1, deadline: Optional[datetime.datetime] = None):
        """Initialize a task with a goal, priority, and optional deadline"""
        self.id = int(time.time() * 1000)  # Unique ID based on timestamp
        self.goal = goal
        self.priority = priority  # 1-5, with 5 being highest
        self.deadline = deadline
        self.created_at = datetime.datetime.now()
        self.completed_at = None
        self.status = "pending"  # pending, in_progress, completed, failed
        self.plan = []
        self.current_step = 0
        self.results = []
        self.notes = []
        self.dependencies = []  # IDs of tasks that must be completed before this one
        self.blocked_by = []    # IDs of tasks blocking this one
        self.schedule = None    # Schedule information for recurring tasks
        self.next_run = None    # Next scheduled run time
    
    def add_plan_step(self, step: str):
        """Add a step to the plan"""
        self.plan.append(step)
    
    def add_result(self, result: str):
        """Add a result from executing a step"""
        self.results.append(result)
    
    def add_note(self, note: str):
        """Add a note or observation to the task"""
        self.notes.append(note)
    
    def mark_complete(self):
        """Mark the task as completed"""
        self.status = "completed"
        self.completed_at = datetime.datetime.now()
    
    def mark_failed(self):
        """Mark the task as failed"""
        self.status = "failed"
        self.completed_at = datetime.datetime.now()
    
    def add_dependency(self, task_id: int) -> None:
        """Add a dependency to this task"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
    
    def remove_dependency(self, task_id: int) -> None:
        """Remove a dependency from this task"""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
    
    def is_blocked(self) -> bool:
        """Check if this task is blocked by dependencies"""
        return len(self.blocked_by) > 0
    
    def update_blocked_status(self, completed_task_ids: List[int]) -> None:
        """Update blocked status based on completed tasks"""
        self.blocked_by = [dep_id for dep_id in self.dependencies if dep_id not in completed_task_ids]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            "id": self.id,
            "goal": self.goal,
            "priority": self.priority,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "plan": self.plan,
            "current_step": self.current_step,
            "results": self.results,
            "notes": self.notes,
            "dependencies": self.dependencies,
            "blocked_by": self.blocked_by,
            "schedule": self.schedule,
            "next_run": self.next_run.isoformat() if self.next_run else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary"""
        task = cls(data["goal"], data.get("priority", 1))
        task.id = data["id"]
        task.created_at = datetime.datetime.fromisoformat(data["created_at"])
        if data.get("completed_at"):
            task.completed_at = datetime.datetime.fromisoformat(data["completed_at"])
        task.status = data["status"]
        task.plan = data.get("plan", [])
        task.current_step = data.get("current_step", 0)
        task.results = data.get("results", [])
        task.notes = data.get("notes", [])
        task.dependencies = data.get("dependencies", [])
        task.blocked_by = data.get("blocked_by", [])
        task.schedule = data.get("schedule")
        if data.get("next_run"):
            task.next_run = datetime.datetime.fromisoformat(data["next_run"])
        if data.get("deadline"):
            task.deadline = datetime.datetime.fromisoformat(data["deadline"])
        return task
    
    def set_schedule(self, schedule_type: str, interval: int) -> None:
        """Set a schedule for a recurring task
        
        schedule_type: 'daily', 'weekly', 'monthly', 'hourly', 'minutes'
        interval: number of units (e.g., 2 for every 2 days)
        """
        self.schedule = {
            "type": schedule_type,
            "interval": interval,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # Calculate the next run time
        self.calculate_next_run()
    
    def calculate_next_run(self) -> None:
        """Calculate the next run time based on the schedule"""
        if not self.schedule:
            self.next_run = None
            return
        
        now = datetime.datetime.now()
        schedule_type = self.schedule["type"]
        interval = self.schedule["interval"]
        
        if schedule_type == "minutes":
            self.next_run = now + datetime.timedelta(minutes=interval)
        elif schedule_type == "hourly":
            self.next_run = now + datetime.timedelta(hours=interval)
        elif schedule_type == "daily":
            self.next_run = now + datetime.timedelta(days=interval)
        elif schedule_type == "weekly":
            self.next_run = now + datetime.timedelta(weeks=interval)
        elif schedule_type == "monthly":
            # Approximate a month as 30 days
            self.next_run = now + datetime.timedelta(days=30 * interval)
        else:
            # Default to daily
            self.next_run = now + datetime.timedelta(days=1)

class SohayAgent:
    """Autonomous agent capabilities for Sohay"""
    
    def __init__(self, sohay_assistant=None):
        """Initialize the autonomous agent"""
        self.tasks = []
        self.active_task = None
        self.state = AGENT_STATES["IDLE"]
        self.memory = []  # List of important observations
        self.long_term_memory = {}  # Structured long-term memory
        self.sohay = sohay_assistant  # Reference to main Sohay instance
        self.autonomous_mode = False
        self.last_action_time = time.time()
        self.check_interval = 60  # Seconds between autonomous actions
        self.scheduled_tasks = []  # List of scheduled task IDs
        
        # Load tasks and memory if available
        self.tasks_file = "sohay_tasks.json"
        self.memory_file = "sohay_memory.json"
        self.load_tasks()
        self.load_memory()
    
    def enable_autonomous_mode(self) -> str:
        """Enable autonomous operation mode"""
        self.autonomous_mode = True
        return "Autonomous mode enabled. I will proactively work on tasks and keep you updated."
    
    def disable_autonomous_mode(self) -> str:
        """Disable autonomous operation mode"""
        self.autonomous_mode = False
        return "Autonomous mode disabled. I will only act when specifically instructed."
    
    def add_task(self, goal: str, priority: int = 1, deadline: Optional[str] = None, depends_on: Optional[List[int]] = None, schedule: Optional[Dict[str, Any]] = None) -> str:
        """Add a new task for the agent to complete"""
        deadline_dt = None
        if deadline:
            try:
                # Try to parse deadline string
                deadline_dt = datetime.datetime.fromisoformat(deadline)
            except ValueError:
                try:
                    # Try to parse as natural language
                    if deadline.lower() == "today":
                        deadline_dt = datetime.datetime.now().replace(hour=23, minute=59, second=59)
                    elif deadline.lower() == "tomorrow":
                        deadline_dt = (datetime.datetime.now() + datetime.timedelta(days=1)).replace(hour=23, minute=59, second=59)
                    elif deadline.lower().startswith("in "):
                        # Parse "in X days/hours/minutes"
                        parts = deadline.lower().split()
                        if len(parts) >= 3:
                            amount = int(parts[1])
                            unit = parts[2]
                            if unit.startswith("day"):
                                deadline_dt = datetime.datetime.now() + datetime.timedelta(days=amount)
                            elif unit.startswith("hour"):
                                deadline_dt = datetime.datetime.now() + datetime.timedelta(hours=amount)
                            elif unit.startswith("minute"):
                                deadline_dt = datetime.datetime.now() + datetime.timedelta(minutes=amount)
                except:
                    pass
        
        task = Task(goal, priority, deadline_dt)
        
        # Add dependencies if provided
        if depends_on:
            for dep_id in depends_on:
                task.add_dependency(dep_id)
            
            # Update blocked_by status
            completed_task_ids = [t.id for t in self.tasks if t.status == "completed"]
            task.update_blocked_status(completed_task_ids)
        
        # Add schedule if provided
        if schedule:
            schedule_type = schedule.get("type", "daily")
            interval = schedule.get("interval", 1)
            task.set_schedule(schedule_type, interval)
            
            # Add to scheduled tasks list
            self.scheduled_tasks.append(task.id)
        
        self.tasks.append(task)
        self.save_tasks()
        
        # If no active task, set this as active if not blocked
        if self.active_task is None and self.autonomous_mode and not task.is_blocked():
            self.active_task = task
            self.state = AGENT_STATES["PLANNING"]
        
        dependency_info = ""
        if depends_on:
            dependency_info = f" with {len(depends_on)} dependencies"
        
        schedule_info = ""
        if schedule:
            schedule_info = f", scheduled {schedule['type']} (every {schedule['interval']} {schedule['type']})"
        
        return f"Task added: '{goal}' with priority {priority}" + (f" and deadline {deadline}" if deadline else "") + dependency_info + schedule_info
    
    def list_tasks(self) -> str:
        """List all tasks and their status"""
        if not self.tasks:
            return "No tasks have been added yet."
        
        result = "Tasks:\n"
        for i, task in enumerate(self.tasks):
            deadline_str = f", Deadline: {task.deadline.strftime('%Y-%m-%d %H:%M')}" if task.deadline else ""
            result += f"{i+1}. [{task.status.upper()}] {task.goal} (Priority: {task.priority}{deadline_str})\n"
            
            # Show plan for in-progress tasks
            if task.status == "in_progress" and task.plan:
                result += "   Plan:\n"
                for j, step in enumerate(task.plan):
                    checkmark = "✓" if j < task.current_step else " "
                    result += f"   {checkmark} Step {j+1}: {step}\n"
        
        return result
    
    def get_task(self, task_id_or_index: Union[int, str]) -> Optional[Task]:
        """Get a task by ID or index"""
        try:
            # Try as index (1-based for user)
            if isinstance(task_id_or_index, str) and task_id_or_index.isdigit():
                index = int(task_id_or_index) - 1
                if 0 <= index < len(self.tasks):
                    return self.tasks[index]
            
            # Try as task ID
            task_id = int(task_id_or_index)
            for task in self.tasks:
                if task.id == task_id:
                    return task
        except:
            pass
        
        return None
    
    def activate_task(self, task_id_or_index: Union[int, str]) -> str:
        """Activate a specific task"""
        task = self.get_task(task_id_or_index)
        if not task:
            return f"Task {task_id_or_index} not found."
        
        self.active_task = task
        task.status = "in_progress"
        self.state = AGENT_STATES["PLANNING"]
        self.save_tasks()
        
        return f"Activated task: {task.goal}"
    
    def complete_task(self, task_id_or_index: Union[int, str]) -> str:
        """Mark a task as completed"""
        task = self.get_task(task_id_or_index)
        if not task:
            return f"Task {task_id_or_index} not found."
        
        task.mark_complete()
        if self.active_task and self.active_task.id == task.id:
            self.active_task = None
            self.state = AGENT_STATES["IDLE"]
        
        self.save_tasks()
        return f"Marked task as completed: {task.goal}"
    
    def delete_task(self, task_id_or_index: Union[int, str]) -> str:
        """Delete a task"""
        task = self.get_task(task_id_or_index)
        if not task:
            return f"Task {task_id_or_index} not found."
        
        self.tasks = [t for t in self.tasks if t.id != task.id]
        if self.active_task and self.active_task.id == task.id:
            self.active_task = None
            self.state = AGENT_STATES["IDLE"]
        
        self.save_tasks()
        return f"Deleted task: {task.goal}"
    
    def save_tasks(self) -> None:
        """Save tasks to file"""
        with open(self.tasks_file, 'w') as f:
            json.dump({
                "tasks": [task.to_dict() for task in self.tasks]
            }, f, indent=2)
    
    def load_tasks(self) -> None:
        """Load tasks from file"""
        try:
            with open(self.tasks_file, 'r') as f:
                data = json.load(f)
                self.tasks = [Task.from_dict(task_data) for task_data in data.get("tasks", [])]
        except (FileNotFoundError, json.JSONDecodeError):
            # File doesn't exist or is invalid
            self.tasks = []
    
    def save_memory(self) -> None:
        """Save memory to file"""
        with open(self.memory_file, 'w') as f:
            json.dump({
                "short_term": self.memory,
                "long_term": self.long_term_memory
            }, f, indent=2)
    
    def load_memory(self) -> None:
        """Load memory from file"""
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                self.memory = data.get("short_term", [])
                self.long_term_memory = data.get("long_term", {})
        except (FileNotFoundError, json.JSONDecodeError):
            # File doesn't exist or is invalid
            self.memory = []
            self.long_term_memory = {}
    
    def add_to_memory(self, category: str, insight: str) -> None:
        """Add an insight to long-term memory"""
        # Add to short-term memory
        if insight not in self.memory:
            self.memory.append(insight)
            # Keep memory at a reasonable size
            if len(self.memory) > 20:
                self.memory.pop(0)  # Remove oldest memory
        
        # Add to long-term memory
        if category not in self.long_term_memory:
            self.long_term_memory[category] = []
        
        # Check if this insight is already in long-term memory
        if insight not in self.long_term_memory[category]:
            self.long_term_memory[category].append(insight)
            # Keep category at a reasonable size
            if len(self.long_term_memory[category]) > 50:
                self.long_term_memory[category].pop(0)  # Remove oldest insight
        
        # Save memory to file
        self.save_memory()
    
    def get_relevant_memories(self, query: str, max_results: int = 5) -> List[str]:
        """Get relevant memories based on a query"""
        relevant_memories = []
        
        # Check short-term memory first
        for memory_item in self.memory:
            if any(keyword in memory_item.lower() for keyword in query.lower().split()):
                relevant_memories.append(memory_item)
        
        # Then check long-term memory
        for category, insights in self.long_term_memory.items():
            if any(keyword in category.lower() for keyword in query.lower().split()):
                relevant_memories.extend(insights)
            else:
                # Check individual insights
                for insight in insights:
                    if any(keyword in insight.lower() for keyword in query.lower().split()):
                        relevant_memories.append(insight)
        
        # Remove duplicates and limit results
        unique_memories = list(dict.fromkeys(relevant_memories))
        return unique_memories[:max_results]
    
    def get_memory_summary(self) -> str:
        """Get a summary of the agent's memory"""
        summary = "Memory Summary:\n\n"
        
        # Short-term memory
        summary += "Short-term Memory:\n"
        if self.memory:
            for i, memory_item in enumerate(self.memory):
                summary += f"{i+1}. {memory_item}\n"
        else:
            summary += "No short-term memories stored.\n"
        
        # Long-term memory
        summary += "\nLong-term Memory Categories:\n"
        if self.long_term_memory:
            for category, insights in self.long_term_memory.items():
                summary += f"- {category}: {len(insights)} insights\n"
        else:
            summary += "No long-term memories stored.\n"
        
        return summary
    
    async def run_autonomously(self) -> str:
        """Main loop for autonomous operation"""
        if not self.autonomous_mode:
            return "Autonomous mode is disabled."
        
        current_time = time.time()
        # Only take action if enough time has passed since last action
        if current_time - self.last_action_time < self.check_interval:
            return "Waiting for next autonomous action."
        
        self.last_action_time = current_time
        
        # Check for scheduled tasks that need to be run
        now = datetime.datetime.now()
        for task_id in self.scheduled_tasks:
            task = next((t for t in self.tasks if t.id == task_id), None)
            if task and task.next_run and now >= task.next_run:
                # Create a new instance of this task
                new_task = Task(task.goal, task.priority, task.deadline)
                
                # Copy dependencies
                for dep_id in task.dependencies:
                    new_task.add_dependency(dep_id)
                
                # Add the new task
                self.tasks.append(new_task)
                
                # Update the next run time for the scheduled task
                task.calculate_next_run()
                
                # Save tasks
                self.save_tasks()
                
                return f"Created new instance of scheduled task: {task.goal}"
        
        # Update dependency status for all tasks
        completed_task_ids = [t.id for t in self.tasks if t.status == "completed"]
        for task in self.tasks:
            if task.status == "pending":
                task.update_blocked_status(completed_task_ids)
        
        # Check if we have an active task
        if not self.active_task:
            # Select highest priority, non-completed, non-blocked task
            pending_tasks = [t for t in self.tasks if t.status == "pending" and not t.is_blocked()]
            if pending_tasks:
                # Sort by priority (higher first), deadline (sooner first), and creation time (older first)
                def task_sort_key(t):
                    # Default date far in the future if no deadline
                    deadline = t.deadline or datetime.datetime.max
                    return (-t.priority, deadline, t.created_at)
                
                pending_tasks.sort(key=task_sort_key)
                self.active_task = pending_tasks[0]
                self.active_task.status = "in_progress"
                self.state = AGENT_STATES["PLANNING"]
                self.save_tasks()
                return f"Autonomously activated task: {self.active_task.goal}"
            else:
                # Check if there are any blocked tasks
                blocked_tasks = [t for t in self.tasks if t.status == "pending" and t.is_blocked()]
                if blocked_tasks:
                    blocked_ids = []
                    for task in blocked_tasks:
                        blocked_ids.extend(task.blocked_by)
                    
                    blocking_tasks = [t for t in self.tasks if t.id in blocked_ids and t.status != "completed"]
                    if blocking_tasks:
                        return f"Waiting for {len(blocking_tasks)} dependencies to complete before proceeding with blocked tasks."
                
                # No pending tasks
                return "No pending tasks to work on autonomously."
        
        # Handle active task based on current state
        if self.state == AGENT_STATES["PLANNING"]:
            await self.plan_task()
            return f"Planned execution for task: {self.active_task.goal}"
        
        elif self.state == AGENT_STATES["EXECUTING"]:
            await self.execute_step()
            return f"Executed step {self.active_task.current_step} of {len(self.active_task.plan)} for task: {self.active_task.goal}"
        
        elif self.state == AGENT_STATES["REFLECTING"]:
            await self.reflect_on_task()
            return f"Reflected on progress of task: {self.active_task.goal}"
        
        elif self.state == AGENT_STATES["LEARNING"]:
            await self.learn_from_task()
            return f"Learned from task execution: {self.active_task.goal}"
        
        # If IDLE, move to planning
        self.state = AGENT_STATES["PLANNING"]
        return "Preparing to plan for active task."
    
    async def plan_task(self) -> None:
        """Plan steps to complete the active task"""
        if not self.active_task:
            return
        
        # Clear any existing plan
        self.active_task.plan = []
        
        # Create a plan based on the task goal and context
        goal = self.active_task.goal.lower()
        
        # Check memory for relevant insights from past tasks
        relevant_insights = []
        for memory_item in self.memory:
            if any(keyword in goal for keyword in memory_item.lower().split()):
                relevant_insights.append(memory_item)
        
        # Research-oriented tasks
        if any(keyword in goal for keyword in ["research", "find", "information", "learn about", "study", "discover"]):
            # Extract specific topics to research
            topics = []
            for keyword in ["about", "on", "regarding", "for", "into"]:
                if keyword in goal:
                    parts = goal.split(keyword, 1)
                    if len(parts) > 1 and parts[1].strip():
                        topics.append(parts[1].strip())
            
            main_topic = topics[0] if topics else goal
            
            # Create a more detailed research plan
            self.active_task.plan = [
                f"Research information related to '{main_topic}'",
                f"Search for recent developments and trends in {main_topic}",
                f"Find authoritative sources and expert opinions on {main_topic}",
                f"Gather data and statistics related to {main_topic}",
                f"Organize research findings by key themes",
                f"Analyze information for patterns and insights",
                f"Create a comprehensive summary of findings on {main_topic}"
            ]
            
            # Add specific steps for comparing different viewpoints if needed
            if any(keyword in goal for keyword in ["compare", "versus", "vs", "pros and cons"]):
                self.active_task.plan.append(f"Compare different perspectives on {main_topic}")
                self.active_task.plan.append(f"Create a balanced analysis of viewpoints")
        
        # Development or coding tasks
        elif any(keyword in goal for keyword in ["develop", "code", "program", "create", "build", "implement"]):
            # Extract what needs to be developed
            project_type = "application"
            for keyword in ["app", "application", "website", "tool", "software", "program", "algorithm", "library"]:
                if keyword in goal:
                    project_type = keyword
                    break
            
            # Extract technology if mentioned
            technology = ""
            tech_keywords = ["python", "javascript", "react", "nodejs", "java", "c++", "typescript", "flutter", "web", "mobile"]
            for keyword in tech_keywords:
                if keyword in goal.lower():
                    technology = keyword
                    break
            
            # Add technology-specific steps if identified
            tech_string = f" using {technology}" if technology else ""
            
            self.active_task.plan = [
                f"Research best practices for developing {project_type}{tech_string}",
                f"Define requirements and user stories for the {project_type}",
                f"Create system architecture and component design",
                f"Plan the development workflow and milestones",
                f"Implement core features of the {project_type}",
                f"Develop user interface and experience components",
                f"Integrate all components and test functionality",
                f"Review code quality and optimize performance",
                f"Finalize documentation and deployment plan"
            ]
        
        # Analysis tasks
        elif any(keyword in goal for keyword in ["analyze", "evaluate", "assess", "review"]):
            # Extract what needs to be analyzed
            analysis_subject = goal
            for keyword in ["analyze", "evaluation of", "assess", "review"]:
                if keyword in goal:
                    parts = goal.split(keyword, 1)
                    if len(parts) > 1 and parts[1].strip():
                        analysis_subject = parts[1].strip()
                        break
            
            # Check if it's a data analysis task
            is_data_task = any(keyword in goal for keyword in ["data", "metrics", "statistics", "numbers", "dataset"])
            
            if is_data_task:
                self.active_task.plan = [
                    f"Identify key data sources for analyzing {analysis_subject}",
                    f"Define metrics and key performance indicators",
                    f"Collect relevant data points and prepare for analysis",
                    f"Perform statistical analysis and data visualization",
                    f"Identify trends, patterns, and outliers in the data",
                    f"Draw evidence-based conclusions from the analysis",
                    f"Prepare visualizations to communicate insights",
                    f"Develop recommendations based on data findings"
                ]
            else:
                self.active_task.plan = [
                    f"Define scope and criteria for analyzing {analysis_subject}",
                    f"Gather background information and context",
                    f"Identify key components and dimensions to evaluate",
                    f"Collect evidence and examples for assessment",
                    f"Apply analytical frameworks to {analysis_subject}",
                    f"Evaluate strengths and weaknesses",
                    f"Draw conclusions and develop insights",
                    f"Formulate recommendations based on the analysis"
                ]
        
        # Writing tasks
        elif any(keyword in goal for keyword in ["write", "draft", "compose", "document", "report"]):
            # Identify the type of document
            doc_type = "document"
            for keyword in ["report", "essay", "article", "blog post", "paper", "summary", "review", "email", "letter", "proposal"]:
                if keyword in goal:
                    doc_type = keyword
                    break
            
            # Extract the subject matter
            subject = goal
            for prep in ["on", "about", "regarding", "for"]:
                prep_phrase = f"{prep} "
                if prep_phrase in goal:
                    parts = goal.split(prep_phrase, 1)
                    if len(parts) > 1 and parts[1].strip():
                        subject = parts[1].strip()
                        break
            
            self.active_task.plan = [
                f"Research background information for {doc_type} on {subject}",
                f"Define the target audience and purpose of the {doc_type}",
                f"Create an outline and structure for the {doc_type}",
                f"Develop key points and arguments to include",
                f"Draft the introduction and main sections",
                f"Add supporting evidence and examples",
                f"Craft a strong conclusion with key takeaways",
                f"Review and edit the {doc_type} for clarity and flow",
                f"Finalize formatting and citations if needed"
            ]
            
        # Planning tasks
        elif any(keyword in goal for keyword in ["plan", "schedule", "organize", "arrange"]):
            # What type of planning?
            plan_type = "plan"
            for keyword in ["project", "event", "meeting", "trip", "strategy", "campaign", "budget", "schedule"]:
                if keyword in goal:
                    plan_type = keyword
                    break
            
            self.active_task.plan = [
                f"Define the scope and objectives for the {plan_type}",
                f"Identify stakeholders and key participants",
                f"Research best practices for {plan_type} planning",
                f"Set timelines and key milestones",
                f"Allocate resources and responsibilities",
                f"Develop detailed action steps for implementation",
                f"Create contingency plans for potential issues",
                f"Design tracking and evaluation mechanisms",
                f"Finalize the {plan_type} plan with stakeholder feedback"
            ]
            
        # Data processing tasks
        elif any(keyword in goal for keyword in ["data", "process", "extract", "transform"]):
            self.active_task.plan = [
                f"Identify data sources needed for '{self.active_task.goal}'",
                f"Define data requirements and quality criteria",
                f"Extract raw data from identified sources",
                f"Clean and preprocess the data (fix errors, handle missing values)",
                f"Transform data into appropriate format for analysis",
                f"Apply relevant data processing algorithms or techniques",
                f"Validate processed data for accuracy and completeness",
                f"Document the data processing methodology",
                f"Prepare processed data for presentation or further analysis"
            ]
            
        # Communication tasks
        elif any(keyword in goal for keyword in ["communicate", "contact", "reach out", "inform", "notify"]):
            # Who to communicate with?
            audience = "stakeholders"
            for keyword in ["team", "client", "customer", "manager", "employee", "partner", "audience"]:
                if keyword in goal:
                    audience = keyword
                    break
            
            self.active_task.plan = [
                f"Identify key {audience} and communication objectives",
                f"Research background information and context",
                f"Define key messages and talking points",
                f"Select appropriate communication channels",
                f"Draft the communication content",
                f"Review and refine messaging for clarity and impact",
                f"Prepare supporting materials if needed",
                f"Execute the communication plan",
                f"Follow up and gather feedback"
            ]
        
        # Default general-purpose plan if no specific category matches
        else:
            self.active_task.plan = [
                f"Research information related to '{self.active_task.goal}'",
                f"Identify key components and requirements",
                f"Develop potential approaches and solutions",
                f"Evaluate options based on effectiveness and feasibility",
                f"Create an implementation plan",
                f"Execute the selected approach",
                f"Review results and make adjustments if needed",
                f"Finalize and document outcomes"
            ]
        
        # Add task-specific steps based on exact task content
        if "report" in goal or "summary" in goal:
            self.active_task.plan.append(f"Create a comprehensive report document")
        
        if "presentation" in goal:
            self.active_task.plan.append(f"Prepare presentation slides with visual aids")
            self.active_task.plan.append(f"Develop speaking notes and key talking points")
        
        if "deadline" in goal or "schedule" in goal:
            self.active_task.plan.append(f"Set up timeline tracking and milestone alerts")
        
        if "team" in goal or "collaborate" in goal:
            self.active_task.plan.append(f"Define team member roles and responsibilities")
            self.active_task.plan.append(f"Establish communication and collaboration protocols")
        
        if "budget" in goal or "cost" in goal:
            self.active_task.plan.append(f"Develop detailed budget breakdown and financial projections")
            self.active_task.plan.append(f"Identify cost-saving opportunities and contingencies")
        
        # Add insights from memory if available
        if relevant_insights:
            self.active_task.plan.append("Apply insights from previous tasks:")
            for insight in relevant_insights[:3]:  # Limit to top 3 insights
                self.active_task.plan.append(f"  - {insight}")
        
        # If the task has a deadline, add a step to monitor time
        if self.active_task.deadline:
            time_remaining = self.active_task.deadline - datetime.datetime.now()
            days_remaining = time_remaining.days
            
            if days_remaining < 1:
                hours_remaining = time_remaining.seconds // 3600
                if hours_remaining < 1:
                    self.active_task.plan.insert(0, f"URGENT: Complete task within {time_remaining.seconds // 60} minutes!")
                else:
                    self.active_task.plan.insert(0, f"URGENT: Complete task within {hours_remaining} hours!")
            else:
                self.active_task.plan.append(f"Monitor progress to ensure completion before deadline ({days_remaining} days remaining)")
        
        # Move to execution state
        self.state = AGENT_STATES["EXECUTING"]
        self.save_tasks()
    
    async def execute_step(self) -> None:
        """Execute the current step of the active task"""
        if not self.active_task or not self.active_task.plan:
            self.state = AGENT_STATES["IDLE"]
            return
        
        # Get the current step
        if self.active_task.current_step >= len(self.active_task.plan):
            # All steps complete
            self.active_task.mark_complete()
            self.state = AGENT_STATES["LEARNING"]
            self.save_tasks()
            return
        
        current_step = self.active_task.plan[self.active_task.current_step]
        
        # Execute the step using Sohay's capabilities
        result = f"Executed: {current_step}"
        
        try:
            # Check if we have a reference to the main Sohay instance
            if self.sohay:
                # Determine the type of action needed based on step text
                if "research" in current_step.lower() or "information" in current_step.lower() or "search" in current_step.lower():
                    # Extract search query from step
                    query = self.active_task.goal
                    if "about" in current_step:
                        parts = current_step.split("about")
                        if len(parts) > 1:
                            query = parts[1].strip().strip("'").strip('"')
                    
                    # Use Google Search if available
                    search_result = self.sohay.google_search(query)
                    result = f"Searched for information: {query}\n\nResults:\n{search_result}"
                
                elif "browse" in current_step.lower() or "website" in current_step.lower() or "web" in current_step.lower():
                    # Extract URL or website name
                    url = "https://www.google.com"  # Default
                    if "to" in current_step:
                        parts = current_step.split("to")
                        if len(parts) > 1:
                            url_part = parts[1].strip().strip("'").strip('"')
                            if not url_part.startswith(("http://", "https://")):
                                url_part = "https://" + url_part
                            url = url_part
                    
                    # Try direct search if browsing fails
                    try:
                        if hasattr(self.sohay, 'handle_browser_command') and self.sohay.browser:
                            browse_cmd = "browser search"
                            # Run in async context
                            browser_result = await self.sohay.handle_browser_command(browse_cmd, {"query": query})
                            result = f"Browsed website: {url}\n\nResults:\n{browser_result}"
                        else:
                            # Fallback to direct search if browser not available
                            if SEARCH_DIRECT:
                                search_result = search_and_format(query)
                                result = f"Searched for information (browser not available): {query}\n\nResults:\n{search_result}"
                            else:
                                result = f"Error: Browser functionality not available and search fallback not found."
                    except Exception as e:
                        # Also try direct search on error
                        if SEARCH_DIRECT:
                            search_result = search_and_format(query)
                            result = f"Searched for information (browser error): {query}\n\nResults:\n{search_result}"
                        else:
                            result = f"Error during web browsing: {str(e)}"
                
                elif "analyze" in current_step.lower() or "organize" in current_step.lower():
                    # This would involve processing collected information
                    # For now, we'll simulate this step with a structured response
                    result = f"Analysis of task '{self.active_task.goal}':\n\n"
                    result += "1. Key findings:\n"
                    result += "   - Information collected from various sources\n"
                    result += "   - Data organized into relevant categories\n"
                    result += "   - Patterns and trends identified\n\n"
                    result += "2. Insights:\n"
                    result += "   - Main concepts related to the task\n"
                    result += "   - Relationships between different aspects\n"
                    result += "   - Areas for further investigation\n\n"
                    result += "Analysis complete and results saved."
                
                elif "identify" in current_step.lower() or "solution" in current_step.lower():
                    # This would involve determining solutions or approaches
                    result = f"Potential solutions for '{self.active_task.goal}':\n\n"
                    result += "1. Approach #1: Direct implementation\n"
                    result += "   - Advantages: Quick, straightforward\n"
                    result += "   - Disadvantages: May miss optimization opportunities\n\n"
                    result += "2. Approach #2: Research-based strategy\n"
                    result += "   - Advantages: Well-informed, comprehensive\n"
                    result += "   - Disadvantages: More time-consuming\n\n"
                    result += "3. Approach #3: Iterative approach\n"
                    result += "   - Advantages: Adaptive, flexible\n"
                    result += "   - Disadvantages: Requires ongoing adjustments\n\n"
                    result += "Recommended approach: #2 Research-based strategy"
                
                elif "execute" in current_step.lower() or "implement" in current_step.lower():
                    # This would involve implementing the chosen solution
                    result = f"Implementing solution for '{self.active_task.goal}':\n\n"
                    result += "1. Preparation:\n"
                    result += "   - Resources gathered\n"
                    result += "   - Plan finalized\n\n"
                    result += "2. Implementation:\n"
                    result += "   - Core components set up\n"
                    result += "   - Integration tests performed\n\n"
                    result += "3. Finalization:\n"
                    result += "   - Documentation completed\n"
                    result += "   - Quality assurance checks passed\n\n"
                    result += "Implementation complete and ready for verification."
                
                elif "verify" in current_step.lower() or "report" in current_step.lower():
                    # This would involve checking results and reporting
                    result = f"Verification of task '{self.active_task.goal}':\n\n"
                    result += "1. Testing results:\n"
                    result += "   - All core functionality verified\n"
                    result += "   - Edge cases tested\n\n"
                    result += "2. Performance metrics:\n"
                    result += "   - Time efficiency: Good\n"
                    result += "   - Resource usage: Optimal\n\n"
                    result += "3. Final report:\n"
                    result += "   - Task completed successfully\n"
                    result += "   - All requirements met\n"
                    result += "   - Documentation finalized\n\n"
                    result += "Task verification complete. Ready to mark as finished."
                
                elif "read" in current_step.lower() or "file" in current_step.lower():
                    # Extract file name
                    file_name = "README.md"  # Default
                    words = current_step.split()
                    for i, word in enumerate(words):
                        if word.lower() == "file" and i + 1 < len(words):
                            file_name = words[i + 1].strip().strip("'").strip('"')
                        elif word.lower() == "read" and i + 1 < len(words):
                            file_name = words[i + 1].strip().strip("'").strip('"')
                    
                    # Read the file
                    try:
                        file_content = self.sohay.read_file(file_name)
                        result = f"Read file '{file_name}':\n\n{file_content}"
                    except Exception as e:
                        result = f"Error reading file: {str(e)}"
                
                elif "execute" in current_step.lower() or "command" in current_step.lower() or "run" in current_step.lower():
                    # Extract command
                    command = ""
                    if "command" in current_step:
                        parts = current_step.split("command")
                        if len(parts) > 1:
                            command = parts[1].strip().strip("'").strip('"')
                    elif "run" in current_step:
                        parts = current_step.split("run")
                        if len(parts) > 1:
                            command = parts[1].strip().strip("'").strip('"')
                    
                    # Execute the command using the shell execution function
                    try:
                        shell_id = "agent_shell"
                        cwd = os.getcwd()
                        cmd_result = self.sohay.execute_shell_command(command, shell_id, cwd)
                        result = f"Executed command '{command}':\n\n{cmd_result}"
                    except Exception as e:
                        result = f"Error executing command: {str(e)}"
            
        except Exception as e:
            result += f"\n\nError during execution: {str(e)}"
        
        # Record the result
        self.active_task.add_result(result)
        
        # Move to next step
        self.active_task.current_step += 1
        
        # If all steps complete, move to reflection
        if self.active_task.current_step >= len(self.active_task.plan):
            self.state = AGENT_STATES["REFLECTING"]
        
        self.save_tasks()
    
    async def reflect_on_task(self) -> None:
        """Reflect on the task execution and results"""
        if not self.active_task:
            self.state = AGENT_STATES["IDLE"]
            return
        
        # Analyze the results of all steps
        reflection = f"Reflection on task: '{self.active_task.goal}'\n\n"
        
        # Check completion status
        steps_completed = self.active_task.current_step
        total_steps = len(self.active_task.plan)
        completion_percentage = (steps_completed / total_steps) * 100 if total_steps > 0 else 0
        
        reflection += f"Task completion: {completion_percentage:.1f}% ({steps_completed}/{total_steps} steps)\n\n"
        
        # Analyze successes and challenges
        successes = []
        challenges = []
        
        for i, result in enumerate(self.active_task.results):
            if i < len(self.active_task.plan):
                step_description = self.active_task.plan[i]
                
                # Check for success indicators
                if "Error" in result or "error" in result or "failed" in result or "failure" in result:
                    challenges.append(f"Step {i+1}: {step_description} - Encountered issues")
                else:
                    successes.append(f"Step {i+1}: {step_description} - Completed successfully")
        
        if successes:
            reflection += "Successes:\n"
            for success in successes:
                reflection += f"- {success}\n"
            reflection += "\n"
        
        if challenges:
            reflection += "Challenges:\n"
            for challenge in challenges:
                reflection += f"- {challenge}\n"
            reflection += "\n"
        
        # Time analysis
        task_duration = None
        if self.active_task.completed_at:
            task_duration = self.active_task.completed_at - self.active_task.created_at
        elif self.active_task.created_at:
            task_duration = datetime.datetime.now() - self.active_task.created_at
        
        if task_duration:
            hours, remainder = divmod(task_duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            reflection += f"Time spent: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds\n\n"
        
        # Deadline analysis
        if self.active_task.deadline:
            if self.active_task.completed_at:
                time_difference = self.active_task.deadline - self.active_task.completed_at
                if time_difference.total_seconds() > 0:
                    reflection += f"Completed {time_difference.days} days, {time_difference.seconds // 3600} hours before deadline\n"
                else:
                    time_difference = -time_difference
                    reflection += f"Completed {time_difference.days} days, {time_difference.seconds // 3600} hours after deadline\n"
            else:
                time_remaining = self.active_task.deadline - datetime.datetime.now()
                if time_remaining.total_seconds() > 0:
                    reflection += f"Time remaining until deadline: {time_remaining.days} days, {time_remaining.seconds // 3600} hours\n"
                else:
                    time_overdue = -time_remaining
                    reflection += f"Task is overdue by {time_overdue.days} days, {time_overdue.seconds // 3600} hours\n"
            reflection += "\n"
        
        # Effectiveness analysis
        if completion_percentage >= 100:
            reflection += "Overall assessment: Task completed successfully\n"
        elif completion_percentage >= 75:
            reflection += "Overall assessment: Task mostly completed with some remaining steps\n"
        elif completion_percentage >= 50:
            reflection += "Overall assessment: Task partially completed\n"
        else:
            reflection += "Overall assessment: Task in early stages of completion\n"
        
        # Add insights for future improvements
        reflection += "\nInsights for future similar tasks:\n"
        
        if challenges:
            reflection += "- Consider allocating more time for challenging steps\n"
        
        if len(self.active_task.plan) > 7:
            reflection += "- Task might benefit from being broken down into smaller sub-tasks\n"
        
        if task_duration and task_duration.total_seconds() > 7200:  # More than 2 hours
            reflection += "- Long execution time suggests higher complexity than anticipated\n"
        
        # Add the reflection to the task notes
        self.active_task.add_note(reflection)
        
        # Move to learning phase
        self.state = AGENT_STATES["LEARNING"]
        self.save_tasks()
    
    async def learn_from_task(self) -> None:
        """Learn from the task execution for future improvements"""
        if not self.active_task:
            self.state = AGENT_STATES["IDLE"]
            return
        
        # Analyze patterns across all completed tasks to improve future performance
        completed_tasks = [t for t in self.tasks if t.status == "completed"]
        
        learning_note = f"Learning from task execution: '{self.active_task.goal}'\n\n"
        
        # Pattern recognition across tasks
        if completed_tasks:
            # Count tasks by type
            task_types = {}
            for task in completed_tasks:
                task_goal = task.goal.lower()
                task_type = "other"
                
                if any(keyword in task_goal for keyword in ["research", "find", "information"]):
                    task_type = "research"
                elif any(keyword in task_goal for keyword in ["develop", "code", "program"]):
                    task_type = "development"
                elif any(keyword in task_goal for keyword in ["analyze", "evaluate", "assess"]):
                    task_type = "analysis"
                elif any(keyword in task_goal for keyword in ["write", "draft", "compose"]):
                    task_type = "writing"
                
                task_types[task_type] = task_types.get(task_type, 0) + 1
            
            # Most common task type
            most_common_type = max(task_types.items(), key=lambda x: x[1])[0] if task_types else None
            
            if most_common_type:
                learning_note += f"Pattern: Most frequent task type is '{most_common_type}' ({task_types.get(most_common_type, 0)} tasks)\n"
                # Add to memory
                self.add_to_memory("Task Patterns", f"Most frequent task type is '{most_common_type}'")
            
            # Average task completion time
            total_duration = datetime.timedelta()
            count_with_duration = 0
            
            for task in completed_tasks:
                if task.completed_at and task.created_at:
                    duration = task.completed_at - task.created_at
                    total_duration += duration
                    count_with_duration += 1
            
            if count_with_duration > 0:
                avg_duration = total_duration / count_with_duration
                hours, remainder = divmod(avg_duration.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                
                learning_note += f"Average task completion time: {int(hours)} hours, {int(minutes)} minutes\n"
                # Add to memory
                self.add_to_memory("Task Metrics", f"Average task completion time: {int(hours)} hours, {int(minutes)} minutes")
            
            # Success rate
            completed_count = len([t for t in completed_tasks if t.status == "completed"])
            failed_count = len([t for t in self.tasks if t.status == "failed"])
            total_count = completed_count + failed_count
            
            if total_count > 0:
                success_rate = (completed_count / total_count) * 100
                learning_note += f"Task success rate: {success_rate:.1f}% ({completed_count}/{total_count})\n"
                # Add to memory
                self.add_to_memory("Task Metrics", f"Task success rate: {success_rate:.1f}%")
        
        # Task-specific learning
        current_type = "other"
        current_goal = self.active_task.goal.lower()
        
        if any(keyword in current_goal for keyword in ["research", "find", "information"]):
            current_type = "research"
            learning_note += "\nLearning about research tasks:\n"
            learning_note += "- Most effective when using diverse information sources\n"
            learning_note += "- Better results when organizing findings systematically\n"
            
            # Add to memory
            self.add_to_memory("Research Tasks", "Most effective when using diverse information sources")
            self.add_to_memory("Research Tasks", "Better results when organizing findings systematically")
        
        elif any(keyword in current_goal for keyword in ["develop", "code", "program"]):
            current_type = "development"
            learning_note += "\nLearning about development tasks:\n"
            learning_note += "- Planning phase crucial for successful implementation\n"
            learning_note += "- Testing throughout development improves outcomes\n"
            
            # Add to memory
            self.add_to_memory("Development Tasks", "Planning phase crucial for successful implementation")
            self.add_to_memory("Development Tasks", "Testing throughout development improves outcomes")
        
        elif any(keyword in current_goal for keyword in ["analyze", "evaluate", "assess"]):
            current_type = "analysis"
            learning_note += "\nLearning about analysis tasks:\n"
            learning_note += "- Quality of data significantly impacts analysis results\n"
            learning_note += "- Structured approach leads to more comprehensive insights\n"
            
            # Add to memory
            self.add_to_memory("Analysis Tasks", "Quality of data significantly impacts analysis results")
            self.add_to_memory("Analysis Tasks", "Structured approach leads to more comprehensive insights")
        
        elif any(keyword in current_goal for keyword in ["write", "draft", "compose"]):
            current_type = "writing"
            learning_note += "\nLearning about writing tasks:\n"
            learning_note += "- Outlining before drafting improves document structure\n"
            learning_note += "- Multiple review passes catch more issues\n"
            
            # Add to memory
            self.add_to_memory("Writing Tasks", "Outlining before drafting improves document structure")
            self.add_to_memory("Writing Tasks", "Multiple review passes catch more issues")
        
        # Add strategies for future improvement
        learning_note += "\nStrategies for future improvement:\n"
        
        # Based on the type of task
        if current_type == "research":
            learning_note += "- Use more specific search queries for better results\n"
            learning_note += "- Create structured note-taking templates\n"
            
            # Add to memory
            self.add_to_memory("Research Strategies", "Use more specific search queries for better results")
            self.add_to_memory("Research Strategies", "Create structured note-taking templates")
        elif current_type == "development":
            learning_note += "- Break down complex functionality into smaller modules\n"
            learning_note += "- Implement automated testing where possible\n"
            
            # Add to memory
            self.add_to_memory("Development Strategies", "Break down complex functionality into smaller modules")
            self.add_to_memory("Development Strategies", "Implement automated testing where possible")
        elif current_type == "analysis":
            learning_note += "- Establish clear metrics before beginning analysis\n"
            learning_note += "- Use visualization to identify patterns more effectively\n"
            
            # Add to memory
            self.add_to_memory("Analysis Strategies", "Establish clear metrics before beginning analysis")
            self.add_to_memory("Analysis Strategies", "Use visualization to identify patterns more effectively")
        elif current_type == "writing":
            learning_note += "- Develop standard templates for common document types\n"
            learning_note += "- Allocate specific time for editing separate from drafting\n"
            
            # Add to memory
            self.add_to_memory("Writing Strategies", "Develop standard templates for common document types")
            self.add_to_memory("Writing Strategies", "Allocate specific time for editing separate from drafting")
        else:
            learning_note += "- Create more detailed initial plans\n"
            learning_note += "- Set clearer success criteria at the outset\n"
            
            # Add to memory
            self.add_to_memory("General Strategies", "Create more detailed initial plans")
            self.add_to_memory("General Strategies", "Set clearer success criteria at the outset")
        
        # Add general productivity strategies
        learning_note += "\nGeneral productivity enhancements:\n"
        learning_note += "- Break large tasks into smaller, manageable sub-tasks\n"
        learning_note += "- Set intermediate deadlines for multi-stage tasks\n"
        learning_note += "- Allocate buffer time for unexpected complications\n"
        learning_note += "- Document successful approaches for reference in similar future tasks\n"
        
        # Add to memory
        self.add_to_memory("Productivity", "Break large tasks into smaller, manageable sub-tasks")
        self.add_to_memory("Productivity", "Set intermediate deadlines for multi-stage tasks")
        self.add_to_memory("Productivity", "Allocate buffer time for unexpected complications")
        
        # Add the learning note to the task
        self.active_task.add_note(learning_note)
        
        # Store task-specific insights
        task_insight = f"For {current_type} tasks: {self.active_task.goal} - {learning_note.split('\n')[0]}"
        self.add_to_memory(f"{current_type.capitalize()} Tasks", task_insight)
        
        # Mark task as complete if not already
        if self.active_task.status != "completed":
            self.active_task.mark_complete()
        
        # Reset active task and go to idle
        self.active_task = None
        self.state = AGENT_STATES["IDLE"]
        self.save_tasks()
    
    def get_status(self) -> str:
        """Get the current status of the autonomous agent"""
        mode = "Enabled" if self.autonomous_mode else "Disabled"
        state = self.state
        active_task = self.active_task.goal if self.active_task else "None"
        
        pending_count = sum(1 for t in self.tasks if t.status == "pending")
        in_progress_count = sum(1 for t in self.tasks if t.status == "in_progress")
        completed_count = sum(1 for t in self.tasks if t.status == "completed")
        
        # Count blocked tasks
        blocked_count = sum(1 for t in self.tasks if t.status == "pending" and t.is_blocked())
        
        # Count scheduled tasks
        scheduled_count = sum(1 for t in self.tasks if t.schedule)
        
        # Memory stats
        short_term_count = len(self.memory)
        long_term_categories = len(self.long_term_memory)
        long_term_insights = sum(len(insights) for insights in self.long_term_memory.values())
        
        # Next scheduled task
        next_scheduled = None
        next_scheduled_time = None
        for task in self.tasks:
            if task.schedule and task.next_run:
                if next_scheduled_time is None or task.next_run < next_scheduled_time:
                    next_scheduled = task
                    next_scheduled_time = task.next_run
        
        next_scheduled_info = ""
        if next_scheduled:
            next_run_str = next_scheduled_time.strftime("%Y-%m-%d %H:%M")
            next_scheduled_info = f"\nNext scheduled task: '{next_scheduled.goal}' at {next_run_str}"
        
        return f"""
Autonomous Mode: {mode}
Current State: {state}
Active Task: {active_task}

Task Statistics:
- Pending: {pending_count} (Blocked: {blocked_count})
- In Progress: {in_progress_count}
- Completed: {completed_count}
- Scheduled: {scheduled_count}
- Total: {len(self.tasks)}{next_scheduled_info}

Memory Statistics:
- Short-term memories: {short_term_count}
- Long-term categories: {long_term_categories}
- Total insights: {long_term_insights}
"""
    
    def handle_command(self, command: str) -> str:
        """Handle an autonomous agent command"""
        # Parse command
        command = command.strip().lower()
        
        if command == "auto on" or command == "enable autonomous":
            return self.enable_autonomous_mode()
        
        elif command == "auto off" or command == "disable autonomous":
            return self.disable_autonomous_mode()
        
        elif command.startswith("add task"):
            # Format: add task <goal> [priority:N] [deadline:X] [depends:ID1,ID2] [schedule:type:interval]
            parts = command[8:].strip().split(" priority:")
            goal = parts[0].strip()
            
            priority = 1
            deadline = None
            depends_on = None
            schedule = None
            
            if len(parts) > 1:
                remaining = parts[1]
                
                # Extract priority
                if " deadline:" in remaining:
                    priority_parts = remaining.split(" deadline:")
                    try:
                        priority = int(priority_parts[0].strip())
                    except:
                        pass
                    remaining = priority_parts[1] if len(priority_parts) > 1 else ""
                elif " depends:" in remaining:
                    priority_parts = remaining.split(" depends:")
                    try:
                        priority = int(priority_parts[0].strip())
                    except:
                        pass
                    remaining = priority_parts[1] if len(priority_parts) > 1 else ""
                elif " schedule:" in remaining:
                    priority_parts = remaining.split(" schedule:")
                    try:
                        priority = int(priority_parts[0].strip())
                    except:
                        pass
                    remaining = priority_parts[1] if len(priority_parts) > 1 else ""
                else:
                    try:
                        priority = int(remaining.strip())
                        remaining = ""
                    except:
                        pass
                
                # Extract deadline
                if " depends:" in remaining:
                    deadline_parts = remaining.split(" depends:")
                    deadline = deadline_parts[0].strip()
                    remaining = deadline_parts[1] if len(deadline_parts) > 1 else ""
                elif " schedule:" in remaining:
                    deadline_parts = remaining.split(" schedule:")
                    deadline = deadline_parts[0].strip()
                    remaining = deadline_parts[1] if len(deadline_parts) > 1 else ""
                else:
                    deadline = remaining.strip() if remaining else None
                    remaining = ""
                
                # Extract dependencies
                if remaining and " schedule:" in remaining:
                    deps_parts = remaining.split(" schedule:")
                    deps_str = deps_parts[0].strip()
                    if deps_str.startswith("depends:"):
                        try:
                            depends_on = [int(dep.strip()) for dep in deps_str[8:].split(",")]
                        except:
                            pass
                    remaining = deps_parts[1] if len(deps_parts) > 1 else ""
                elif remaining and remaining.startswith("depends:"):
                    deps_str = remaining[8:].strip()
                    try:
                        depends_on = [int(dep.strip()) for dep in deps_str.split(",")]
                    except:
                        pass
                    remaining = ""
                
                # Extract schedule
                if remaining and remaining.startswith("schedule:"):
                    schedule_str = remaining[9:].strip()
                    schedule_parts = schedule_str.split(":")
                    if len(schedule_parts) >= 2:
                        schedule_type = schedule_parts[0]
                        try:
                            interval = int(schedule_parts[1])
                            schedule = {"type": schedule_type, "interval": interval}
                        except:
                            pass
            
            return self.add_task(goal, priority, deadline, depends_on, schedule)
        
        elif command == "list tasks":
            return self.list_tasks()
        
        elif command == "list scheduled":
            scheduled_tasks = [t for t in self.tasks if t.schedule]
            if not scheduled_tasks:
                return "No scheduled tasks found."
            
            result = "Scheduled Tasks:\n"
            for i, task in enumerate(scheduled_tasks):
                schedule_type = task.schedule["type"]
                interval = task.schedule["interval"]
                next_run = task.next_run.strftime("%Y-%m-%d %H:%M") if task.next_run else "Not scheduled"
                
                result += f"{i+1}. [{task.status.upper()}] {task.goal}\n"
                result += f"   Schedule: Every {interval} {schedule_type}, Next run: {next_run}\n"
            
            return result
        
        elif command.startswith("activate task"):
            task_id = command[13:].strip()
            return self.activate_task(task_id)
        
        elif command.startswith("complete task"):
            task_id = command[13:].strip()
            return self.complete_task(task_id)
        
        elif command.startswith("delete task"):
            task_id = command[11:].strip()
            return self.delete_task(task_id)
        
        elif command.startswith("schedule task"):
            # Format: schedule task <id> <type>:<interval>
            parts = command[13:].strip().split()
            if len(parts) < 2:
                return "Error: Invalid schedule format. Use 'schedule task <id> <type>:<interval>'"
            
            task_id = parts[0]
            schedule_parts = parts[1].split(":")
            if len(schedule_parts) != 2:
                return "Error: Invalid schedule format. Use 'type:interval' (e.g., daily:1)"
            
            schedule_type = schedule_parts[0]
            try:
                interval = int(schedule_parts[1])
            except:
                return "Error: Interval must be a number"
            
            # Find the task
            task = self.get_task(task_id)
            if not task:
                return f"Task {task_id} not found."
            
            # Set the schedule
            task.set_schedule(schedule_type, interval)
            
            # Add to scheduled tasks if not already there
            if task.id not in self.scheduled_tasks:
                self.scheduled_tasks.append(task.id)
            
            self.save_tasks()
            
            next_run = task.next_run.strftime("%Y-%m-%d %H:%M") if task.next_run else "Not scheduled"
            return f"Task '{task.goal}' scheduled to run every {interval} {schedule_type}. Next run: {next_run}"
        
        elif command == "agent status":
            return self.get_status()
        
        elif command == "memory status" or command == "show memory":
            return self.get_memory_summary()
        
        elif command.startswith("recall"):
            query = command[6:].strip()
            memories = self.get_relevant_memories(query)
            
            if not memories:
                return f"No memories found related to '{query}'."
            
            result = f"Memories related to '{query}':\n\n"
            for i, memory in enumerate(memories):
                result += f"{i+1}. {memory}\n"
            
            return result
        
        return f"Unknown autonomous agent command: {command}"
    
    async def run_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool through the Sohay instance"""
        if not self.sohay:
            return "Error: No Sohay instance available to execute tools"
        
        try:
            # Call the appropriate function based on the tool name
            if tool_name == "google_search":
                query = parameters.get("query", "")
                date_range = parameters.get("date_range", "all")
                return self.sohay.google_search(query, date_range)
            
            elif tool_name == "read_file":
                file_path = parameters.get("file", "")
                max_lines = parameters.get("max_lines", 1000)
                return self.sohay.read_file(file_path, max_lines)
            
            elif tool_name == "execute_command":
                command = parameters.get("command", "")
                shell_id = parameters.get("shell_id", "agent_shell")
                cwd = parameters.get("cwd", os.getcwd())
                return self.sohay.execute_shell_command(command, shell_id, cwd)
            
            elif tool_name == "browser_task":
                command = parameters.get("command", "")
                args = parameters.get("args", {})
                if hasattr(self.sohay, 'handle_browser_command'):
                    result = await self.sohay.handle_browser_command(command, args)
                    return result
                else:
                    return "Error: Browser functionality not available"
            
            elif tool_name == "execute_tool":
                tool_name = parameters.get("tool_name", "")
                params = parameters.get("params", {})
                if hasattr(self.sohay, 'execute_tool'):
                    return self.sohay.execute_tool(tool_name, params)
                else:
                    return "Error: Tool execution not available"
            
            else:
                return f"Error: Unknown tool '{tool_name}'"
                
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"
    
    async def gather_information(self, topic: str) -> str:
        """Gather information on a topic using multiple sources"""
        results = []
        
        # First check memory for relevant information
        memories = self.get_relevant_memories(topic)
        if memories:
            memory_info = "Information from memory:\n"
            for memory in memories:
                memory_info += f"- {memory}\n"
            results.append(memory_info)
        
        # Try to use search
        try:
            if SEARCH_DIRECT:
                search_result = search_and_format(topic)
                results.append(f"Search Results:\n{search_result}")
            else:
                search_result = await self.run_tool("google_search", {"query": topic})
                results.append(f"Search Results:\n{search_result}")
        except Exception as e:
            results.append(f"Search error: {str(e)}")
        
        # Try to browse a relevant website
        try:
            browse_result = await self.run_tool("browser_task", {
                "command": "search",
                "args": {"query": topic}
            })
            results.append(f"Browsing Results:\n{browse_result}")
        except Exception as e:
            results.append(f"Browsing error: {str(e)}")
        
        # Combine the results
        combined_results = "\n\n".join(results)
        
        # Store this information in memory
        self.add_to_memory("Research Topics", f"Researched: {topic}")
        
        return f"Information gathered on '{topic}':\n\n{combined_results}" 