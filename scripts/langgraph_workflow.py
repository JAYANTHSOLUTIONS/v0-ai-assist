"""LangGraph workflow orchestration for the travel assistant."""
import json
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import Graph, StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from loguru import logger

from models import (
    IntentType, ExtractedEntities, FlightSearchRequest, 
    HotelSearchRequest, AssistantResponse, UIElement
)
from deepseek_client import deepseek_client
from external_apis import external_apis
from database import db_manager, MessageCreate

class WorkflowState(TypedDict):
    """State object for the LangGraph workflow."""
    session_id: str
    user_id: Optional[str]
    user_input: str
    conversation_history: List[str]
    intent: Optional[IntentType]
    entities: Dict[str, Any]
    confidence: float
    api_results: Optional[List[Dict[str, Any]]]
    response_message: str
    ui_elements: List[UIElement]
    error: Optional[str]

class TravelAssistantWorkflow:
    """LangGraph workflow for orchestrating the travel assistant."""
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("preprocess_input", self.preprocess_input)
        workflow.add_node("extract_intent", self.extract_intent_and_entities)
        workflow.add_node("route_request", self.route_request)
        workflow.add_node("search_flights", self.search_flights)
        workflow.add_node("search_hotels", self.search_hotels)
        workflow.add_node("create_booking", self.create_booking)
        workflow.add_node("handle_general", self.handle_general_inquiry)
        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("store_conversation", self.store_conversation)
        
        # Set entry point
        workflow.set_entry_point("preprocess_input")
        
        # Add edges
        workflow.add_edge("preprocess_input", "extract_intent")
        workflow.add_edge("extract_intent", "route_request")
        
        # Conditional routing based on intent
        workflow.add_conditional_edges(
            "route_request",
            self.route_condition,
            {
                "search_flight": "search_flights",
                "search_hotel": "search_hotels",
                "book_trip": "create_booking",
                "general": "handle_general"
            }
        )
        
        # All paths lead to response generation
        workflow.add_edge("search_flights", "generate_response")
        workflow.add_edge("search_hotels", "generate_response")
        workflow.add_edge("create_booking", "generate_response")
        workflow.add_edge("handle_general", "generate_response")
        
        # Final steps
        workflow.add_edge("generate_response", "store_conversation")
        workflow.add_edge("store_conversation", END)
        
        return workflow.compile()
    
    async def preprocess_input(self, state: WorkflowState) -> WorkflowState:
        """Preprocess and clean user input."""
        logger.info(f"Preprocessing input for session: {state['session_id']}")
        
        # Clean and normalize input
        cleaned_input = state["user_input"].strip()
        
        # Load conversation history from database
        try:
            db = db_manager.get_db()
            history = db_manager.get_conversation_history(
                db, state["session_id"], limit=10
            )
            
            conversation_history = []
            for msg in reversed(history):  # Reverse to get chronological order
                conversation_history.append(f"{msg.message_type}: {msg.content}")
            
            state["conversation_history"] = conversation_history
            db.close()
            
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
            state["conversation_history"] = []
        
        state["user_input"] = cleaned_input
        return state
    
    async def extract_intent_and_entities(self, state: WorkflowState) -> WorkflowState:
        """Extract intent and entities using DeepSeek LLM."""
        logger.info("Extracting intent and entities")
        
        try:
            extracted = await deepseek_client.extract_intent_and_entities(
                state["user_input"],
                state["conversation_history"]
            )
            
            state["intent"] = extracted.intent
            state["entities"] = extracted.entities
            state["confidence"] = extracted.confidence
            
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            state["intent"] = IntentType.GENERAL_INQUIRY
            state["entities"] = {}
            state["confidence"] = 0.5
            state["error"] = str(e)
        
        return state
    
    def route_condition(self, state: WorkflowState) -> str:
        """Determine routing based on extracted intent."""
        intent = state["intent"]
        
        if intent == IntentType.SEARCH_FLIGHT:
            return "search_flight"
        elif intent == IntentType.SEARCH_HOTEL:
            return "search_hotel"
        elif intent == IntentType.BOOK_TRIP:
            return "book_trip"
        else:
            return "general"
    
    async def route_request(self, state: WorkflowState) -> WorkflowState:
        """Route request based on intent (placeholder for routing logic)."""
        logger.info(f"Routing request with intent: {state['intent']}")
        return state
    
    async def search_flights(self, state: WorkflowState) -> WorkflowState:
        """Handle flight search requests."""
        logger.info("Processing flight search")
        
        try:
            entities = state["entities"]
            
            # Create flight search request from entities
            flight_request = FlightSearchRequest(
                origin=entities.get("origin", ""),
                destination=entities.get("destination", ""),
                departure_date=entities.get("departure_date", ""),
                return_date=entities.get("return_date"),
                passengers=int(entities.get("passengers", 1)),
                class_type=entities.get("class_type", "economy")
            )
            
            # Call external flight API
            flights = await external_apis.search_flights(flight_request)
            
            # Convert to dict for JSON serialization
            state["api_results"] = [flight.dict() for flight in flights]
            
        except Exception as e:
            logger.error(f"Flight search failed: {e}")
            state["error"] = str(e)
            state["api_results"] = []
        
        return state
    
    async def search_hotels(self, state: WorkflowState) -> WorkflowState:
        """Handle hotel search requests."""
        logger.info("Processing hotel search")
        
        try:
            entities = state["entities"]
            
            # Create hotel search request from entities
            hotel_request = HotelSearchRequest(
                location=entities.get("location", ""),
                check_in=entities.get("check_in", ""),
                check_out=entities.get("check_out", ""),
                guests=int(entities.get("guests", 1)),
                rooms=int(entities.get("rooms", 1))
            )
            
            # Call external hotel API
            hotels = await external_apis.search_hotels(hotel_request)
            
            # Convert to dict for JSON serialization
            state["api_results"] = [hotel.dict() for hotel in hotels]
            
        except Exception as e:
            logger.error(f"Hotel search failed: {e}")
            state["error"] = str(e)
            state["api_results"] = []
        
        return state
    
    async def create_booking(self, state: WorkflowState) -> WorkflowState:
        """Handle booking creation requests."""
        logger.info("Processing booking request")
        
        try:
            entities = state["entities"]
            booking_type = entities.get("booking_type", "flight")
            item_id = entities.get("booking_id", "")
            
            # Create booking
            booking = await external_apis.create_booking(
                booking_type, item_id, entities
            )
            
            state["api_results"] = [booking.dict()]
            
        except Exception as e:
            logger.error(f"Booking creation failed: {e}")
            state["error"] = str(e)
            state["api_results"] = []
        
        return state
    
    async def handle_general_inquiry(self, state: WorkflowState) -> WorkflowState:
        """Handle general inquiries and greetings."""
        logger.info("Processing general inquiry")
        
        # For general inquiries, we don't need external API calls
        state["api_results"] = []
        return state
    
    async def generate_response(self, state: WorkflowState) -> WorkflowState:
        """Generate natural language response using DeepSeek LLM."""
        logger.info("Generating response")
        
        try:
            response_data = await deepseek_client.generate_response(
                state["user_input"],
                state["intent"],
                state["entities"],
                state["api_results"],
                state["conversation_history"]
            )
            
            state["response_message"] = response_data["message"]
            state["ui_elements"] = response_data["ui_elements"]
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            state["response_message"] = "I apologize, but I'm having trouble processing your request right now."
            state["ui_elements"] = []
            state["error"] = str(e)
        
        return state
    
    async def store_conversation(self, state: WorkflowState) -> WorkflowState:
        """Store conversation in database."""
        logger.info("Storing conversation")
        
        try:
            db = db_manager.get_db()
            
            # Store user message
            user_message = MessageCreate(
                session_id=state["session_id"],
                user_id=state["user_id"],
                message_type="user",
                content=state["user_input"],
                metadata={
                    "intent": state["intent"].value if state["intent"] else None,
                    "entities": state["entities"],
                    "confidence": state["confidence"]
                }
            )
            db_manager.create_message(db, user_message)
            
            # Store assistant response
            assistant_message = MessageCreate(
                session_id=state["session_id"],
                user_id=state["user_id"],
                message_type="assistant",
                content=state["response_message"],
                metadata={
                    "ui_elements": [elem.dict() for elem in state["ui_elements"]],
                    "api_results_count": len(state["api_results"]) if state["api_results"] else 0
                }
            )
            db_manager.create_message(db, assistant_message)
            
            # Update session
            db_manager.create_or_update_session(
                db, state["session_id"], state["user_id"]
            )
            
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            state["error"] = str(e)
        
        return state
    
    async def run_workflow(
        self, 
        user_input: str, 
        session_id: str, 
        user_id: Optional[str] = None
    ) -> AssistantResponse:
        """Run the complete workflow."""
        logger.info(f"Starting workflow for session: {session_id}")
        
        initial_state = WorkflowState(
            session_id=session_id,
            user_id=user_id,
            user_input=user_input,
            conversation_history=[],
            intent=None,
            entities={},
            confidence=0.0,
            api_results=None,
            response_message="",
            ui_elements=[],
            error=None
        )
        
        try:
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Create response
            response = AssistantResponse(
                message=final_state["response_message"],
                intent=final_state["intent"],
                entities=final_state["entities"],
                results=final_state["api_results"],
                ui_elements=final_state["ui_elements"],
                session_id=session_id
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            # Return error response
            return AssistantResponse(
                message="I apologize, but I encountered an error processing your request. Please try again.",
                session_id=session_id
            )

# Global workflow instance
travel_workflow = TravelAssistantWorkflow()
