"""
Loan Approval Agent using LangChain
Processes loan applications based on policy documents
"""

import os
import json
from typing import Dict, List, Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Data models
class LoanApplication(BaseModel):
    applicantId: str
    requestedAmount: float
    annualIncome: float
    monthlyDebt: float
    creditScore: int
    employmentMonths: int
    isFirstTimeBuyer: bool
    isSelfEmployed: bool

class LoanDecision(BaseModel):
    decision: str = Field(description="Either 'approved' or 'denied'")
    reasoning: str = Field(description="Detailed explanation of the decision")
    riskLevel: str = Field(description="Risk level: 'low', 'medium', or 'high'")
    appliedRules: List[str] = Field(description="List of rules that were applied")

class LoanAgent:
    def __init__(self, openai_api_key: str = None, model_name: str = "gpt-3.5-turbo"):
        """Initialize the loan approval agent"""
        # Use provided key or load from environment
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass as parameter.")
        
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model_name=model_name,
            temperature=0
        )
        
        # Initialize output parser
        self.output_parser = PydanticOutputParser(pydantic_object=LoanDecision)
        
        # Create the main prompt template
        self.main_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a loan approval expert. You will receive a policy document and loan application data.

            Your task:
            1. Extract loan approval rules from the policy document
            2. Apply those rules to the loan application
            3. Make a decision with detailed reasoning

            Policy Document:
            {policy_text}

            {format_instructions}

            Guidelines for decision making:
            1. Calculate debt-to-income ratio: (monthly_debt * 12) / annual_income
            2. Determine risk level based on credit score ranges in the policy
            3. Apply appropriate DTI limits for the risk level
            4. Check special cases (first-time buyer, self-employed)
            5. Provide clear reasoning for your decision"""),
            ("human", """Loan Application Data:
            {application_data}

            Please analyze the policy and make a loan decision.""")
        ])
    
    def load_policy_text(self, pdf_path: str) -> str:
        """Load policy PDF and return as text"""
        try:
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Combine all pages into single text
            policy_text = "\n\n".join([doc.page_content for doc in documents])
            
            print(f"Loaded policy document: {len(policy_text)} characters")
            return policy_text
            
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return ""
    
    def process_loan_application(self, pdf_path: str, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processing a loan application"""
        
        # 1. Load policy text
        policy_text = self.load_policy_text(pdf_path)
        if not policy_text:
            return {
                "decision": "denied",
                "reasoning": "Error loading policy document",
                "riskLevel": "high",
                "appliedRules": ["Error handling rule"]
            }
        
        # 2. Create application object
        application = LoanApplication(**application_data)
        
        # 3. Process through prompt → LLM → parser
        try:
            # Format the prompt
            formatted_prompt = self.main_prompt.format_messages(
                policy_text=policy_text,
                application_data=json.dumps(application.dict(), indent=2),
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Get LLM response
            llm_response = self.llm.invoke(formatted_prompt)
            
            # Parse the response
            decision = self.output_parser.parse(llm_response.content)
            
            # 4. Return result
            return {
                "decision": decision.decision,
                "reasoning": decision.reasoning,
                "riskLevel": decision.riskLevel,
                "appliedRules": decision.appliedRules
            }
            
        except Exception as e:
            print(f"Error processing application: {e}")
            return {
                "decision": "denied",
                "reasoning": f"Error processing application: {str(e)}",
                "riskLevel": "high",
                "appliedRules": ["Error handling rule"]
            }
