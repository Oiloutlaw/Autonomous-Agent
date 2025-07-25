import os
import time
import threading
import multiprocessing
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from dotenv import load_dotenv

from replication_manager import ReplicationManager
from revenue_engines import RevenueOrchestrator
from SelfHealingLauncher import (
    shared_data,
    check_youtube_monetization,
    upload_to_youtube,
    trend_scanner,
    script_writer,
    thumbnail_designer,
    video_creator,
    uploader,
    seo_optimizer,
    monetization_checker,
    crew,
)

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedAutonomousAgent:
    """Enhanced autonomous agent with self-replication and multi-revenue capabilities"""

    def __init__(self, instance_id: str = None, specialization: str = 'general'):
        self.instance_id = instance_id or f"agent-{int(time.time())}"
        self.specialization = specialization
        self.replication_manager = None
        self.revenue_orchestrator = RevenueOrchestrator(self.instance_id)
        self.is_master = instance_id is None  # Master instance manages replication
        self.running = True

        self.performance_metrics = {
            "cycles_completed": 0,
            "total_revenue": 0.0,
            "uptime_start": datetime.now(),
            "last_heartbeat": datetime.now(),
        }

        logger.info(
            f"Initialized Enhanced Agent: {self.instance_id} (specialization: {specialization})"
        )

    def initialize_replication_manager(self):
        """Initialize replication manager (only for master instance)"""
        if self.is_master:
            try:
                self.replication_manager = ReplicationManager()
                logger.info("Replication manager initialized")
            except Exception as e:
                logger.error(f"Failed to initialize replication manager: {e}")
                self.replication_manager = None

    def execute_specialized_cycle(self) -> dict:
        """Execute revenue generation cycle based on specialization"""
        try:
            if self.specialization == 'youtube':
                return self.revenue_orchestrator.execute_youtube_cycle()
            elif self.specialization == 'affiliate':
                return self.revenue_orchestrator.execute_affiliate_cycle()
            elif self.specialization == 'digital_products':
                return self.revenue_orchestrator.execute_digital_product_cycle()
            elif self.specialization == 'services':
                return self.revenue_orchestrator.execute_service_cycle()
            else:
                return self.revenue_orchestrator.execute_revenue_cycle()
        except Exception as e:
            logger.error(f"Specialized cycle failed: {e}")
            return {"error": str(e), "estimated_revenue": 0}

    def execute_crewai_pipeline(self) -> dict:
        """Execute the original CrewAI pipeline"""
        try:
            logger.info("🚀 Starting CrewAI pipeline...")

            result = crew.kickoff()

            shared_data["log"].append(f"CrewAI pipeline completed at {datetime.now()}")

            estimated_revenue = 50.0  # Base revenue for completing pipeline

            return {
                "type": "crewai_pipeline",
                "result": str(result),
                "estimated_revenue": estimated_revenue,
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"CrewAI pipeline failed: {e}")
            return {"error": str(e), "estimated_revenue": 0}

    def update_performance_metrics(self, cycle_result: dict):
        """Update performance metrics based on cycle results"""
        self.performance_metrics["cycles_completed"] += 1
        self.performance_metrics["total_revenue"] += cycle_result.get("total_revenue_generated", 0)
        self.performance_metrics["last_heartbeat"] = datetime.now()

        shared_data["revenue"] = self.performance_metrics["total_revenue"]
        shared_data["log"].append(
            f"Agent {self.instance_id}: Cycle {self.performance_metrics['cycles_completed']} "
            f"completed, Revenue: ${self.performance_metrics['total_revenue']:.2f}"
        )

        if self.replication_manager:
            self.replication_manager.update_instance_metrics(
                self.instance_id,
                cycle_result.get("total_revenue_generated", 0),
                1,  # One task completed
            )

    def send_heartbeat_to_master(self):
        """Send heartbeat to master instance (for non-master instances)"""
        if not self.is_master:
            try:
                logger.debug(f"Heartbeat from {self.instance_id}")
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {e}")

    def run_autonomous_loop(self):
        """Main autonomous operation loop"""
        logger.info(f"🤖 Starting autonomous loop for {self.instance_id}")

        cycle_count = 0
        while self.running:
            try:
                cycle_start = time.time()
                logger.info(f"🔄 Starting cycle {cycle_count + 1}")

                revenue_result = self.execute_specialized_cycle()

                crewai_result = self.execute_crewai_pipeline()

                combined_result = {
                    "cycle_number": cycle_count + 1,
                    "revenue_activities": revenue_result,
                    "crewai_result": crewai_result,
                    "total_revenue_generated": (
                        revenue_result.get("total_revenue_generated", 0)
                        + crewai_result.get("estimated_revenue", 0)
                    ),
                    "cycle_duration": time.time() - cycle_start,
                }

                self.update_performance_metrics(combined_result)

                self.send_heartbeat_to_master()

                cycle_count += 1

                logger.info(
                    f"✅ Cycle {cycle_count} completed. "
                    f"Revenue: ${combined_result['total_revenue_generated']:.2f}, "
                    f"Duration: {combined_result['cycle_duration']:.1f}s"
                )

                if shared_data.get("paused", False):
                    logger.info("⏸️ Agent paused, waiting...")
                    while shared_data.get("paused", False) and self.running:
                        time.sleep(10)
                    logger.info("▶️ Agent resumed")

                base_wait = 1800  # 30 minutes
                performance_multiplier = max(
                    0.5, min(2.0, 1.0 / max(0.1, self.performance_metrics["total_revenue"] / 100))
                )
                wait_time = base_wait * performance_multiplier

                logger.info(f"⏳ Waiting {wait_time/60:.1f} minutes before next cycle...")
                time.sleep(wait_time)

            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal, shutting down...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Error in autonomous loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error

    def get_status(self) -> dict:
        """Get current agent status"""
        uptime = datetime.now() - self.performance_metrics["uptime_start"]

        return {
            "instance_id": self.instance_id,
            "specialization": self.specialization,
            "is_master": self.is_master,
            "running": self.running,
            "uptime_seconds": uptime.total_seconds(),
            "performance_metrics": self.performance_metrics,
            "revenue_summary": self.revenue_orchestrator.get_revenue_summary(),
        }


enhanced_app = Flask(__name__)

agent_instance = None


@enhanced_app.route("/metrics")
def metrics():
    """Enhanced metrics endpoint"""
    base_metrics = {
        "revenue": shared_data.get("revenue", 0),
        "funnels": shared_data.get("funnels", []),
        "log": shared_data.get("log", []),
        "paused": shared_data.get("paused", False),
    }

    if agent_instance:
        agent_status = agent_instance.get_status()
        base_metrics.update({"agent_status": agent_status, "enhanced_features": True})

    return jsonify(base_metrics)


@enhanced_app.route("/status")
def status():
    """Get detailed agent status"""
    if agent_instance:
        return jsonify(agent_instance.get_status())
    return jsonify({"error": "Agent not initialized"})


@enhanced_app.route("/toggle", methods=["POST"])
def toggle():
    """Toggle agent pause state"""
    shared_data["paused"] = not shared_data["paused"]
    return jsonify({"paused": shared_data["paused"]})


@enhanced_app.route("/revenue_summary")
def revenue_summary():
    """Get detailed revenue summary"""
    if agent_instance:
        return jsonify(agent_instance.revenue_orchestrator.get_revenue_summary())
    return jsonify({"error": "Agent not initialized"})


@enhanced_app.route("/replication_status")
def replication_status():
    """Get replication manager status"""
    if agent_instance and agent_instance.replication_manager:
        return jsonify(agent_instance.replication_manager.get_instance_stats())
    return jsonify({"error": "Replication manager not available"})


@enhanced_app.route("/spawn_instance", methods=["POST"])
def spawn_instance():
    """Manually spawn new instance"""
    if agent_instance and agent_instance.replication_manager:
        data = request.get_json() or {}
        specialization = data.get("specialization", "general")
        instance_id = agent_instance.replication_manager.spawn_instance(specialization)
        return jsonify({"instance_id": instance_id, "success": instance_id is not None})
    return jsonify({"error": "Replication manager not available"})


def main():
    """Enhanced main function"""
    global agent_instance

    instance_id = os.getenv("INSTANCE_ID")
    specialization = os.getenv("SPECIALIZATION", "general")

    agent_instance = EnhancedAutonomousAgent(instance_id, specialization)

    if agent_instance.is_master:
        agent_instance.initialize_replication_manager()

        if agent_instance.replication_manager:
            replication_thread = threading.Thread(
                target=agent_instance.replication_manager.run_replication_loop, daemon=True
            )
            replication_thread.start()
            logger.info("🔄 Replication management started")

    flask_thread = threading.Thread(
        target=lambda: enhanced_app.run(host="0.0.0.0", port=8000, debug=False), daemon=True
    )
    flask_thread.start()
    logger.info("🌐 Enhanced metrics server started on port 8000")

    time.sleep(2)

    # Initial monetization check
    shared_data["monetization"] = check_youtube_monetization()

    try:
        agent_instance.run_autonomous_loop()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Enhanced Autonomous Agent...")
        agent_instance.running = False
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
