#!/usr/bin/env python3
"""
Script to generate a comprehensive report on Bangladesh's economy using
GPT-4o-mini for analysis and writing.
"""

import os
import sys
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify OpenAI API key is set
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    print("Error: OPENAI_API_KEY not found in environment variables.")
    print("Please add your OpenAI API key to the .env file.")
    sys.exit(1)

# Import OpenAI API client
try:
    from openai import OpenAI
except ImportError:
    print("Error: Could not import OpenAI module.")
    print("Please install it with: pip install openai")
    sys.exit(1)

# Configure OpenAI API client
client = OpenAI(api_key=openai_api_key)

def generate_section(topic, context=""):
    """Generate a report section using GPT-4o-mini"""
    print(f"Generating report section for: {topic}")
    
    prompt = f"""
    You are writing a comprehensive report on Bangladesh's economy in 2025.
    
    Write a detailed, well-structured section (approximately 300-400 words) 
    focusing specifically on: {topic}
    
    Include relevant data, statistics, trends, and analysis. 
    Base your analysis on the most recent available data and reasonable projections.
    
    If you mention specific data points, cite the possible source (like World Bank, IMF, ADB, or Bangladesh Bank).
    
    Additional context: {context}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert economic analyst specializing in South Asian economies. Your task is to write a detailed, factual, and insightful report section on Bangladesh's economy in 2025."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating report with GPT-4o-mini: {e}")
        return f"[Error generating content for {topic}: {str(e)}]"

def compile_full_report(sections):
    """Compile all sections into a complete report"""
    print("Compiling full report...")
    
    # Assemble the full report
    full_report = f"""
# Bangladesh Economy in 2025: A Comprehensive Analysis

## Introduction
{sections["Introduction"]}

## GDP Growth Projections for 2025
{sections["GDP Growth Projections"]}

## Inflation Rates and Projections
{sections["Inflation Rates"]}

## Export Sectors with Focus on RMG Industry
{sections["Export Sectors"]}

## Remittance Flows and Trends
{sections["Remittance Flows"]}

## Foreign Currency Reserves Status
{sections["Foreign Currency Reserves"]}

## Major Economic Challenges
{sections["Economic Challenges"]}

## Conclusion and Future Outlook
{sections["Conclusion"]}

---
*This report was generated using AI analysis based on historical economic data, trends, and projections. 
While efforts have been made to ensure accuracy, readers should consult official sources for the most 
current economic data.*
"""
    return full_report

def main():
    """Main function to coordinate the report generation process"""
    print("\n" + "="*60)
    print("Bangladesh Economy in 2025 - Report Generator")
    print("="*60 + "\n")
    
    print("This script will generate a comprehensive 2000-word report on Bangladesh's economy.")
    print("It will use GPT-4o-mini to analyze and structure the content.\n")
    
    # Topics to cover in the report
    topics = {
        "Introduction": "Introduction to Bangladesh's Economy in 2025, including historical context and key indicators",
        "GDP Growth Projections": "Bangladesh GDP growth projections for 2025, including factors driving growth",
        "Inflation Rates": "Bangladesh inflation rates and projections for 2025, including monetary policy considerations",
        "Export Sectors": "Bangladesh export sectors with focus on RMG industry performance in 2025, including competitive position",
        "Remittance Flows": "Bangladesh remittance flows and trends in 2025, including major source countries",
        "Foreign Currency Reserves": "Bangladesh foreign currency reserves status in 2025, including management strategies",
        "Economic Challenges": "Major economic challenges facing Bangladesh in 2025, including potential solutions",
        "Conclusion": "Conclusion and future outlook for Bangladesh's economy beyond 2025"
    }
    
    # Generate report sections
    print("Generating report sections...")
    sections = {}
    
    # First generate introduction
    sections["Introduction"] = generate_section(topics["Introduction"])
    
    # Generate middle sections
    for topic, description in list(topics.items())[1:-1]:
        sections[topic] = generate_section(description)
        time.sleep(1)  # Avoid rate limiting
    
    # Generate conclusion with context from other sections
    all_content = "\n\n".join([sections[topic] for topic in list(topics.keys())[:-1]])
    sections["Conclusion"] = generate_section(topics["Conclusion"], 
                                             f"This should summarize key points from the report and provide future outlook. Context from other sections: {all_content[:1000]}")
    
    # Compile the full report
    full_report = compile_full_report(sections)
    
    # Save the report to a file
    output_file = "Bangladesh_Economy_2025_Report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_report)
    
    print(f"\nReport generation complete!")
    print(f"The report has been saved to: {output_file}")
    print("\n" + "="*60)

if __name__ == "__main__":
    main() 