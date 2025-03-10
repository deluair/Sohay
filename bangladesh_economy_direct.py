#!/usr/bin/env python3
"""
Script to generate a comprehensive report on Bangladesh's economy using
GPT-4o-mini directly, without relying on search functionality.
"""

import os
import sys
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

def generate_report():
    """Generate a comprehensive report on Bangladesh's economy"""
    print("\n" + "="*60)
    print("Bangladesh Economy in 2025 - Direct Report Generator")
    print("="*60 + "\n")
    
    print("This script will generate a comprehensive 2000-word report on Bangladesh's economy.")
    print("It will use GPT-4o-mini to generate the content directly.\n")
    
    # Define the system prompt
    system_prompt = """
    You are an expert economic analyst specializing in South Asian economies, particularly Bangladesh.
    Your task is to create a comprehensive, well-structured 2000-word report on Bangladesh's economy in 2025.
    
    The report should:
    1. Be based on reasonable projections from current economic trends and data
    2. Include specific sections on GDP growth, inflation, export sectors (especially RMG), remittances, foreign currency reserves, and economic challenges
    3. Cite potential sources like World Bank, IMF, ADB, and Bangladesh Bank where appropriate
    4. Use a formal, analytical tone appropriate for an economic report
    5. Include relevant statistics and data points with reasonable projections for 2025
    6. Provide a balanced view of challenges and opportunities
    
    Format the report with clear headings, subheadings, and a professional structure.
    """
    
    # Define the user prompt
    user_prompt = """
    Please write a comprehensive 2000-word report on Bangladesh's economy in 2025, covering the following topics:
    
    1. Introduction to Bangladesh's economy and its position in South Asia
    2. GDP growth projections for 2025, including factors driving growth
    3. Inflation rates and projections for 2025, including monetary policy considerations
    4. Export sectors with focus on RMG industry performance in 2025
    5. Remittance flows and trends in 2025, including major source countries
    6. Foreign currency reserves status in 2025
    7. Major economic challenges facing Bangladesh in 2025, including climate change impacts
    8. Conclusion and future outlook
    
    Format the report with clear headings and sections. Include relevant economic data and cite sources like World Bank, IMF, ADB, and Bangladesh Bank where appropriate.
    """
    
    print("Generating report...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=3000,
            temperature=0.7
        )
        
        report = response.choices[0].message.content
        
        # Save the report to a file
        output_file = "Bangladesh_Economy_2025_Direct_Report.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\nReport generation complete!")
        print(f"The report has been saved to: {output_file}")
        
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        sys.exit(1)
    
    print("\n" + "="*60)

if __name__ == "__main__":
    generate_report() 