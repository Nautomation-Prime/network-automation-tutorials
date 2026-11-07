import subprocess
import time
import socket
from contextlib import contextmanager
from nornir.core.task import Task, Result

@contextmanager
def ssh_tunnel(bastion_host, bastion_user, target_host, target_port=22, local_port=None):
    """
    Create SSH tunnel: localhost:local_port -> bastion -> target_host:target_port
    """
    
    if local_port is None:
        # Find a free local port
        sock = socket.socket()
        sock.bind(('', 0))
        local_port = sock.getsockname()[1]
        sock.close()
    
    # Start SSH tunnel
    tunnel_cmd = [
        'ssh',
        '-L', f'{local_port}:{target_host}:{target_port}',
        f'{bastion_user}@{bastion_host}',
        'sleep 3600'  # Keep tunnel open for 1 hour
    ]
    
    print(f"Opening tunnel: localhost:{local_port} -> {bastion_host} -> {target_host}:{target_port}")
    
    tunnel_process = subprocess.Popen(
        tunnel_cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    
    # Give tunnel time to establish
    time.sleep(2)
    
    try:
        yield local_port
    finally:
        # Close tunnel
        tunnel_process.terminate()
        tunnel_process.wait(timeout=5)
        print(f"Closed tunnel: localhost:{local_port}")

# Usage in tasks:
def backup_via_tunnel(task: Task) -> Result:
    """Backup device via SSH tunnel through bastion"""
    
    bastion = "bastion.example.com"
    bastion_user = "netadmin"
    target_device = task.host.hostname  # 10.1.1.1
    
    with ssh_tunnel(bastion, bastion_user, target_device) as local_port:
        # Connect to device through tunnel (localhost:local_port)
        from netmiko import ConnectHandler
        
        device = {
            'device_type': 'cisco_ios',
            'host': '127.0.0.1',
            'port': local_port,
            'username': task.host.username,
            'password': task.host.password,
        }
        
        with ConnectHandler(**device) as net_connect:
            config = net_connect.send_command('show running-config')
        
        return Result(
            host=task.host,
            result={'config': config}
        )
