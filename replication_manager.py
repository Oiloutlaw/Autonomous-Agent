import os
import time
import json
import threading
import subprocess
import multiprocessing
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import redis
import sqlite3
from flask import Flask, jsonify, request
import docker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentInstance:
    """Represents a single agent instance"""

    instance_id: str
    created_at: datetime
    status: str  # 'active', 'idle', 'error', 'terminated'
    revenue_generated: float
    tasks_completed: int
    specialization: str  # 'youtube', 'affiliate', 'digital_products', etc.
    performance_score: float
    last_heartbeat: datetime
    container_id: Optional[str] = None
    port: Optional[int] = None


class ReplicationManager:
    """Manages the creation, monitoring, and optimization of agent instances"""

    def __init__(self, redis_host='localhost', redis_port=6379):
        self.instances: Dict[str, AgentInstance] = {}
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.docker_client = docker.from_env()
        self.db_path = 'replication_memory.db'
        self.base_port = 8001
        self.max_instances = 10
        self.revenue_threshold = 1000  # Spawn new instance when existing ones generate $1k
        self.performance_threshold = 0.7  # Minimum performance score to keep instance

        self.init_database()
        self.load_existing_instances()

    def init_database(self):
        """Initialize the replication tracking database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS instances (
                instance_id TEXT PRIMARY KEY,
                created_at TEXT,
                status TEXT,
                revenue_generated REAL,
                tasks_completed INTEGER,
                specialization TEXT,
                performance_score REAL,
                last_heartbeat TEXT,
                container_id TEXT,
                port INTEGER
            )
        '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS replication_events (
                timestamp TEXT,
                event_type TEXT,
                instance_id TEXT,
                details TEXT
            )
        '''
        )
        conn.commit()
        conn.close()

    def load_existing_instances(self):
        """Load existing instances from database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM instances WHERE status != "terminated"')
        rows = c.fetchall()

        for row in rows:
            instance = AgentInstance(
                instance_id=row[0],
                created_at=datetime.fromisoformat(row[1]),
                status=row[2],
                revenue_generated=row[3],
                tasks_completed=row[4],
                specialization=row[5],
                performance_score=row[6],
                last_heartbeat=datetime.fromisoformat(row[7]),
                container_id=row[8],
                port=row[9],
            )
            self.instances[instance.instance_id] = instance

        conn.close()
        logger.info(f"Loaded {len(self.instances)} existing instances")

    def save_instance(self, instance: AgentInstance):
        """Save instance to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            '''
            INSERT OR REPLACE INTO instances VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            (
                instance.instance_id,
                instance.created_at.isoformat(),
                instance.status,
                instance.revenue_generated,
                instance.tasks_completed,
                instance.specialization,
                instance.performance_score,
                instance.last_heartbeat.isoformat(),
                instance.container_id,
                instance.port,
            ),
        )
        conn.commit()
        conn.close()

    def log_event(self, event_type: str, instance_id: str, details: str):
        """Log replication events"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            '''
            INSERT INTO replication_events VALUES (?, ?, ?, ?)
        ''',
            (datetime.now().isoformat(), event_type, instance_id, details),
        )
        conn.commit()
        conn.close()

    def generate_instance_id(self) -> str:
        """Generate unique instance ID"""
        timestamp = int(time.time())
        return f"agent-{timestamp}-{len(self.instances)}"

    def get_available_port(self) -> int:
        """Get next available port for new instance"""
        used_ports = {instance.port for instance in self.instances.values() if instance.port}
        for port in range(self.base_port, self.base_port + 100):
            if port not in used_ports:
                return port
        raise Exception("No available ports")

    def spawn_instance(self, specialization: str = 'general') -> str:
        """Spawn a new agent instance"""
        if len(self.instances) >= self.max_instances:
            logger.warning("Maximum instances reached, cannot spawn new instance")
            return None

        instance_id = self.generate_instance_id()
        port = self.get_available_port()

        instance = AgentInstance(
            instance_id=instance_id,
            created_at=datetime.now(),
            status='initializing',
            revenue_generated=0.0,
            tasks_completed=0,
            specialization=specialization,
            performance_score=1.0,
            last_heartbeat=datetime.now(),
            port=port,
        )

        try:
            container = self.docker_client.containers.run(
                'autonomous-agent:latest',
                detach=True,
                ports={f'8000/tcp': port},
                environment={
                    'INSTANCE_ID': instance_id,
                    'SPECIALIZATION': specialization,
                    'REPLICATION_MANAGER_HOST': 'host.docker.internal',
                },
                name=f"agent-{instance_id}",
            )

            instance.container_id = container.id
            instance.status = 'active'

            self.instances[instance_id] = instance
            self.save_instance(instance)
            self.log_event('spawn', instance_id, f'Spawned with specialization: {specialization}')

            logger.info(f"Spawned new instance: {instance_id} on port {port}")
            return instance_id

        except Exception as e:
            logger.error(f"Failed to spawn instance: {e}")
            instance.status = 'error'
            self.save_instance(instance)
            return None

    def terminate_instance(self, instance_id: str):
        """Terminate an agent instance"""
        if instance_id not in self.instances:
            logger.warning(f"Instance {instance_id} not found")
            return

        instance = self.instances[instance_id]

        try:
            if instance.container_id:
                container = self.docker_client.containers.get(instance.container_id)
                container.stop()
                container.remove()

            instance.status = 'terminated'
            self.save_instance(instance)
            self.log_event('terminate', instance_id, 'Instance terminated')

            logger.info(f"Terminated instance: {instance_id}")

        except Exception as e:
            logger.error(f"Failed to terminate instance {instance_id}: {e}")

    def update_instance_metrics(self, instance_id: str, revenue: float, tasks: int):
        """Update instance performance metrics"""
        if instance_id not in self.instances:
            return

        instance = self.instances[instance_id]
        instance.revenue_generated += revenue
        instance.tasks_completed += tasks
        instance.last_heartbeat = datetime.now()

        if instance.tasks_completed > 0:
            instance.performance_score = instance.revenue_generated / instance.tasks_completed

        self.save_instance(instance)

        self.redis_client.hset(
            f"instance:{instance_id}",
            mapping={
                'revenue': instance.revenue_generated,
                'tasks': instance.tasks_completed,
                'performance': instance.performance_score,
                'last_update': datetime.now().isoformat(),
            },
        )

    def should_replicate(self) -> bool:
        """Determine if new instances should be spawned"""
        if len(self.instances) >= self.max_instances:
            return False

        total_revenue = sum(instance.revenue_generated for instance in self.instances.values())
        active_instances = len([i for i in self.instances.values() if i.status == 'active'])

        if active_instances == 0:
            return True  # Always spawn first instance

        avg_revenue_per_instance = total_revenue / active_instances if active_instances > 0 else 0

        return avg_revenue_per_instance > self.revenue_threshold

    def optimize_instances(self):
        """Optimize instance performance and terminate underperforming ones"""
        for instance_id, instance in list(self.instances.items()):
            if (datetime.now() - instance.last_heartbeat).seconds > 600:
                logger.warning(f"Instance {instance_id} appears stale, terminating")
                self.terminate_instance(instance_id)
                continue

            if (
                instance.performance_score < self.performance_threshold
                and instance.tasks_completed > 10
            ):  # Give instances time to prove themselves
                logger.info(f"Terminating underperforming instance: {instance_id}")
                self.terminate_instance(instance_id)
                continue

    def get_instance_stats(self) -> Dict:
        """Get comprehensive statistics about all instances"""
        active_instances = [i for i in self.instances.values() if i.status == 'active']
        total_revenue = sum(i.revenue_generated for i in self.instances.values())
        total_tasks = sum(i.tasks_completed for i in self.instances.values())

        specializations = {}
        for instance in active_instances:
            spec = instance.specialization
            if spec not in specializations:
                specializations[spec] = {'count': 0, 'revenue': 0}
            specializations[spec]['count'] += 1
            specializations[spec]['revenue'] += instance.revenue_generated

        return {
            'total_instances': len(self.instances),
            'active_instances': len(active_instances),
            'total_revenue': total_revenue,
            'total_tasks': total_tasks,
            'avg_performance': (
                sum(i.performance_score for i in active_instances) / len(active_instances)
                if active_instances
                else 0
            ),
            'specializations': specializations,
            'instances': [asdict(instance) for instance in self.instances.values()],
        }

    def run_replication_loop(self):
        """Main replication management loop"""
        logger.info("Starting replication management loop")

        while True:
            try:
                self.optimize_instances()

                if self.should_replicate():
                    specializations = ['youtube', 'affiliate', 'digital_products', 'services']
                    best_spec = max(
                        specializations,
                        key=lambda s: sum(
                            i.performance_score
                            for i in self.instances.values()
                            if i.specialization == s
                        )
                        or 0,
                    )

                    self.spawn_instance(best_spec)

                time.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in replication loop: {e}")
                time.sleep(60)  # Wait 1 minute on error


replication_app = Flask(__name__)
replication_manager = ReplicationManager()


@replication_app.route('/instances')
def get_instances():
    return jsonify(replication_manager.get_instance_stats())


@replication_app.route('/spawn', methods=['POST'])
def spawn_instance():
    data = request.get_json() or {}
    specialization = data.get('specialization', 'general')
    instance_id = replication_manager.spawn_instance(specialization)
    return jsonify({'instance_id': instance_id, 'success': instance_id is not None})


@replication_app.route('/terminate/<instance_id>', methods=['POST'])
def terminate_instance(instance_id):
    replication_manager.terminate_instance(instance_id)
    return jsonify({'success': True})


@replication_app.route('/metrics/<instance_id>', methods=['POST'])
def update_metrics(instance_id):
    data = request.get_json()
    revenue = data.get('revenue', 0)
    tasks = data.get('tasks', 0)
    replication_manager.update_instance_metrics(instance_id, revenue, tasks)
    return jsonify({'success': True})


if __name__ == '__main__':
    replication_thread = threading.Thread(
        target=replication_manager.run_replication_loop, daemon=True
    )
    replication_thread.start()

    replication_app.run(host='0.0.0.0', port=9000)
