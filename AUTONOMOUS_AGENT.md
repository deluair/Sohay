# Sohay Autonomous Agent

This document explains how to use Sohay's new autonomous agent capabilities, which transform it from a reactive assistant into a proactive autonomous agent that can work on tasks in the background.

## What is an Autonomous Agent?

An autonomous agent is an AI system that can:

1. **Take initiative** - Work on tasks without constant user prompting
2. **Plan and execute** - Break down complex goals into actionable steps
3. **Remember context** - Maintain state across multiple interactions
4. **Self-prioritize** - Decide what to work on based on importance and deadlines
5. **Learn and adapt** - Improve based on past experiences

## How to Use the Autonomous Agent

### Enabling the Agent

When you start Sohay, you'll be asked if you want to enable autonomous mode:
```
Would you like to enable autonomous agent mode? (y/n):
```

You can also enable/disable it manually:
```
You: auto on
```
or
```
You: auto off
```

### Managing Tasks

The agent works on tasks that you assign to it. Here's how to manage tasks:

#### Adding Tasks

```
You: add task Research the latest advancements in quantum computing
```

With priority (1-5, higher means more important):
```
You: add task Create a summary of climate change research priority:4
```

With deadline:
```
You: add task Book flight tickets priority:5 deadline:tomorrow
```

Natural language deadlines supported:
- "today"
- "tomorrow"
- "in 3 days"
- "in 2 hours"
- "in 30 minutes"
- Or ISO format (YYYY-MM-DD HH:MM:SS)

#### Listing Tasks

```
You: list tasks
```

This will show all tasks with their status, priority, and deadline (if any).

#### Activating a Specific Task

By default, the agent will choose the highest priority task. To manually activate a task:

```
You: activate task 2
```
(where 2 is the task number shown in the task list)

#### Completing or Deleting Tasks

```
You: complete task 3
```

```
You: delete task 1
```

### Agent Status

To see the current status of the agent:

```
You: agent status
```

This shows:
- If autonomous mode is enabled
- The current state (planning, executing, etc.)
- The active task
- Statistics about all tasks

### Starting and Stopping the Agent Thread

The autonomous agent runs in a background thread that periodically checks and works on tasks:

```
You: agent start
```

```
You: agent stop
```

## How the Agent Works

### States

The agent works through a series of states:

1. **IDLE** - Waiting for tasks to be assigned
2. **PLANNING** - Breaking down a task into manageable steps
3. **EXECUTING** - Working on steps one at a time
4. **REFLECTING** - Reviewing the results
5. **LEARNING** - Recording what worked for future tasks

### Task Execution

When working on a task, the agent:

1. Selects the highest priority task
2. Creates a plan with specific steps
3. Executes each step, recording results
4. Reflects on the process
5. Marks the task as completed

## Integration with Sohay's Capabilities

The autonomous agent leverages Sohay's existing capabilities:

- **Web Browsing** - Researches information online
- **File Operations** - Creates and modifies documents
- **API Access** - Retrieves real-time data
- **Command Execution** - Runs necessary commands
- **Natural Language Processing** - Understands complex instructions

## Best Practices

1. **Be specific with tasks** - Clearer tasks get better results
2. **Use priorities** - Help the agent focus on what's important
3. **Set realistic deadlines** - Give the agent enough time to work
4. **Check progress regularly** - Use `list tasks` to monitor status
5. **Start small** - Begin with simple tasks before complex ones

## Limitations

The current version has some limitations:

1. Task execution is simulated (will be enhanced in future versions)
2. No long-term memory across restarts (unless tasks are saved)
3. Limited handling of very complex tasks
4. May occasionally need user guidance for ambiguous steps

## Future Enhancements

Planned improvements:

1. True autonomous execution of steps
2. Learning from past task execution
3. Better handling of complex, multi-stage tasks
4. Integration with calendar and scheduling
5. Proactive suggestions based on observed patterns 