"""
WebSocket endpoints for real-time simulation updates
"""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import logging

from app.core.simulation_manager import SimulationManager
from app.api.deps import get_simulation_manager
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/simulations/{simulation_id}")
async def websocket_simulation_updates(
    websocket: WebSocket,
    simulation_id: str,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
):
    """
    WebSocket endpoint for real-time simulation updates
    
    Args:
        websocket: WebSocket connection
        simulation_id: Simulation identifier
        simulation_manager: Simulation manager dependency
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for simulation {simulation_id}")
    
    try:
        # Add connection to manager
        simulation_manager.add_websocket_connection(simulation_id, websocket)
        
        # Send initial state if simulation exists
        try:
            if simulation_id in simulation_manager.simulations:
                initial_state = simulation_manager.get_simulation_state(simulation_id)
                await websocket.send_text(initial_state.model_dump_json())
                logger.debug(f"Sent initial state for simulation {simulation_id}")
        except Exception as e:
            logger.warning(f"Could not send initial state for {simulation_id}: {e}")
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages with timeout to implement heartbeat
                message = await asyncio.wait_for(
                    websocket.receive_text(), 
                    timeout=settings.WEBSOCKET_HEARTBEAT_INTERVAL
                )
                
                # Handle client messages (heartbeat, commands, etc.)
                await handle_websocket_message(websocket, simulation_id, message, simulation_manager)
                
            except asyncio.TimeoutError:
                # Send heartbeat ping
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                    logger.debug(f"Sent heartbeat ping to simulation {simulation_id}")
                except Exception as e:
                    logger.warning(f"Failed to send heartbeat to {simulation_id}: {e}")
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected from simulation {simulation_id}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for simulation {simulation_id}")
    except Exception as e:
        logger.error(f"WebSocket error for simulation {simulation_id}: {e}")
        try:
            await websocket.close(code=1011, reason=f"Server error: {str(e)}")
        except Exception:
            pass
    finally:
        # Remove connection from manager
        simulation_manager.remove_websocket_connection(simulation_id, websocket)
        logger.info(f"Cleaned up WebSocket connection for simulation {simulation_id}")


async def handle_websocket_message(
    websocket: WebSocket, 
    simulation_id: str, 
    message: str,
    simulation_manager: SimulationManager
):
    """
    Handle incoming WebSocket messages from clients
    
    Args:
        websocket: WebSocket connection
        simulation_id: Simulation identifier
        message: Received message
        simulation_manager: Simulation manager
    """
    try:
        import json
        data = json.loads(message)
        message_type = data.get('type', 'unknown')
        
        logger.debug(f"Received WebSocket message type '{message_type}' for simulation {simulation_id}")
        
        if message_type == 'heartbeat':
            # Respond to client heartbeat
            response = {
                'type': 'heartbeat_response',
                'timestamp': data.get('timestamp'),
                'simulation_id': simulation_id
            }
            await websocket.send_text(json.dumps(response))
            
        elif message_type == 'get_status':
            # Send current simulation status
            if simulation_id in simulation_manager.simulations:
                state = simulation_manager.get_simulation_state(simulation_id)
                await websocket.send_text(state.model_dump_json())
            else:
                error_response = {
                    'type': 'error',
                    'message': f'Simulation {simulation_id} not found'
                }
                await websocket.send_text(json.dumps(error_response))
                
        elif message_type == 'subscribe_statistics':
            # Client wants detailed statistics updates
            if simulation_id in simulation_manager.simulations:
                simulation = simulation_manager.simulations[simulation_id]
                stats = simulation.get_summary_statistics()
                response = {
                    'type': 'statistics',
                    'data': stats
                }
                await websocket.send_text(json.dumps(response))
                
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")
            
    except json.JSONDecodeError:
        # Handle non-JSON messages (could be simple text commands)
        if message.lower() == 'ping':
            await websocket.send_text('pong')
        elif message.lower() == 'status':
            if simulation_id in simulation_manager.simulations:
                state = simulation_manager.get_simulation_state(simulation_id)
                await websocket.send_text(state.model_dump_json())
        else:
            logger.warning(f"Unknown WebSocket message: {message}")
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        try:
            error_response = {
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            }
            await websocket.send_text(json.dumps(error_response))
        except Exception:
            pass


@router.websocket("/ws/health")
async def websocket_health_check(websocket: WebSocket):
    """
    WebSocket health check endpoint
    
    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()
    logger.info("Health check WebSocket connected")
    
    try:
        await websocket.send_text(json.dumps({
            'type': 'health',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }))
        
        # Keep connection open for testing
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if message.lower() == 'health':
                    await websocket.send_text(json.dumps({
                        'type': 'health_response',
                        'status': 'healthy',
                        'timestamp': datetime.now().isoformat()
                    }))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info("Health check WebSocket disconnected")
    except Exception as e:
        logger.error(f"Health check WebSocket error: {e}")
    finally:
        logger.info("Health check WebSocket connection closed")


# Import required modules
import json
from datetime import datetime