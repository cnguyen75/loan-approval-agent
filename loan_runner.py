#!/usr/bin/env python3
"""
Simple Loan Approval Runner
Allows users to input PDF path and loan application data, then outputs JSON result
"""

import os
import json
import sys
from pathlib import Path
from loanagent import LoanAgent

def get_user_input():
    """Get user input for PDF path and loan application data"""
    print("Loan Approval AI Agent - Interactive Runner")
    print("=" * 50)
    
    # Get PDF path
    while True:
        pdf_path = input("\nEnter PDF policy file path (or press Enter for 'loan_policy.pdf'): ").strip()
        if not pdf_path:
            pdf_path = "loan_policy.pdf"
        
        if os.path.exists(pdf_path):
            break
        else:
            print(f"File not found: {pdf_path}")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                sys.exit(1)
    
    print(f"Using policy file: {pdf_path}")
    
    # Get loan application data
    print("\nEnter Loan Application Data:")
    print("-" * 30)
    
    try:
        applicant_id = input("Applicant ID: ").strip() or "APP_USER_001"
        requested_amount = float(input("Requested Amount ($): ") or "250000")
        annual_income = float(input("Annual Income ($): ") or "75000")
        monthly_debt = float(input("Monthly Debt ($): ") or "2000")
        credit_score = int(input("Credit Score: ") or "700")
        employment_months = int(input("Employment Months: ") or "24")
        is_first_time = input("First-time buyer? (y/n): ").strip().lower() == 'y'
        is_self_employed = input("Self-employed? (y/n): ").strip().lower() == 'y'
        
        application_data = {
            "applicantId": applicant_id,
            "requestedAmount": requested_amount,
            "annualIncome": annual_income,
            "monthlyDebt": monthly_debt,
            "creditScore": credit_score,
            "employmentMonths": employment_months,
            "isFirstTimeBuyer": is_first_time,
            "isSelfEmployed": is_self_employed
        }
        
        return pdf_path, application_data
        
    except ValueError as e:
        print(f"Invalid input: {e}")
        sys.exit(1)

def display_application_summary(application_data):
    """Display a summary of the application data"""
    dti = application_data["monthlyDebt"] * 12 / application_data["annualIncome"] * 100
    
    print("\nApplication Summary:")
    print("-" * 25)
    print(f"Applicant ID: {application_data['applicantId']}")
    print(f"Requested Amount: ${application_data['requestedAmount']:,.2f}")
    print(f"Annual Income: ${application_data['annualIncome']:,.2f}")
    print(f"Monthly Debt: ${application_data['monthlyDebt']:,.2f}")
    print(f"Debt-to-Income: {dti:.1f}%")
    print(f"Credit Score: {application_data['creditScore']}")
    print(f"Employment: {application_data['employmentMonths']} months")
    print(f"First-time Buyer: {'Yes' if application_data['isFirstTimeBuyer'] else 'No'}")
    print(f"Self-employed: {'Yes' if application_data['isSelfEmployed'] else 'No'}")

def main():
    """Main function"""
    try:
        # Check for API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OPENAI_API_KEY environment variable not set")
            print("Please set your OpenAI API key:")
            print("export OPENAI_API_KEY='your-api-key-here'")
            sys.exit(1)
        
        # Get user input
        pdf_path, application_data = get_user_input()
        
        # Display summary
        display_application_summary(application_data)
        
        # Initialize agent
        print("\nInitializing AI Agent...")
        agent = LoanAgent(api_key)
        
        # Process application
        print("Processing loan application...")
        result = agent.process_loan_application(pdf_path, application_data)
        
        # Display results
        print("\n" + "=" * 50)
        print("LOAN DECISION RESULT")
        print("=" * 50)
        
        # Print the decision
        print(f"\nDecision: {result['decision'].upper()}")
        print(f"Risk Level: {result['riskLevel'].upper()}")
        print(f"Applied Rules: {len(result['appliedRules'])} rules")
        
        print(f"\nReasoning:")
        print(f"{result['reasoning']}")
        
        print(f"\nApplied Rules:")
        for i, rule in enumerate(result['appliedRules'], 1):
            print(f"   {i}. {rule}")
        
        # Output JSON
        print("\n" + "=" * 50)
        print("JSON OUTPUT")
        print("=" * 50)
        print(json.dumps(result, indent=2))
        
        # Save to file
        output_file = f"loan_decision_{application_data['applicantId']}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResult saved to: {output_file}")
        
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
