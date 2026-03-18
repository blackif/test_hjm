#!/usr/bin/env python3
"""
connection_pool.py
SAP RFC 连接池管理

功能:
- 创建和维护 RFC 连接池
- 连接健康检查
- 自动重连机制
- 连接超时管理
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

try:
    import pyrfc
    from pyrfc import Connection
except ImportError:
    print("警告：pyrfc 未安装，连接池功能不可用")
    pyrfc = None
    Connection = None

CONFIG_DIR = os.path.expanduser("~/.sap-agent")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
PERFORMANCE_FILE = os.path.join(CONFIG_DIR, "performance.json")
POOL_STATE_FILE = os.path.join(CONFIG_DIR, "pool_state.json")


class ConnectionPool:
    """SAP RFC 连接池"""
    
    def __init__(self, max_connections: int = 5, idle_timeout: int = 300):
        """
        初始化连接池
        
        Args:
            max_connections: 最大连接数
            idle_timeout: 空闲超时时间（秒）
        """
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout
        self._pool: list = []
        self._in_use: set = set()
        self._lock = threading.Lock()
        self._config: Optional[Dict] = None
        self._created_at = datetime.now()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if self._config is None:
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception:
                self._config = {}
        return self._config
    
    def _load_performance_config(self) -> Dict:
        """加载性能配置"""
        try:
            if os.path.exists(PERFORMANCE_FILE):
                with open(PERFORMANCE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {
            "connection_pool": {
                "max_connections": self.max_connections,
                "idle_timeout": self.idle_timeout,
                "health_check_interval": 60
            }
        }
    
    def _create_connection(self) -> Optional[Connection]:
        """创建新的 RFC 连接"""
        config = self._load_config()
        sap_config = config.get("sap", {})
        
        if not sap_config:
            print("错误：SAP 配置未找到")
            return None
        
        mode = sap_config.get("mode", "direct")
        
        try:
            if mode == "saprouter":
                # SAProuter 模式
                ashost = sap_config.get("ashost", "")
                if not ashost or not ashost.startswith("/H/"):
                    # 构建 SAProuter 字符串
                    router_host = sap_config.get("saprouter_host", "")
                    router_port = sap_config.get("saprouter_port", "3299")
                    target_host = sap_config.get("ashost", "")
                    ashost = f"/H/{router_host}/S/{router_port}/H/{target_host}"
                
                conn = Connection(
                    ashost=ashost,
                    sysnr=sap_config.get("sysnr", "00"),
                    client=sap_config.get("client", "800"),
                    user=os.environ.get("SAP_USER", ""),
                    passwd=os.environ.get("SAP_PASSWORD", ""),
                    lang=sap_config.get("lang", "ZH"),
                    timeout=30
                )
            else:
                # 直连模式
                conn = Connection(
                    ashost=sap_config.get("ashost", ""),
                    sysnr=sap_config.get("sysnr", "00"),
                    client=sap_config.get("client", "800"),
                    user=os.environ.get("SAP_USER", ""),
                    passwd=os.environ.get("SAP_PASSWORD", ""),
                    lang=sap_config.get("lang", "ZH"),
                    timeout=30
                )
            
            return conn
            
        except Exception as e:
            print(f"创建连接失败：{e}")
            return None
    
    def _is_healthy(self, conn: Connection) -> bool:
        """检查连接是否健康"""
        if conn is None:
            return False
        try:
            conn.ping()
            return True
        except Exception:
            return False
    
    def get_connection(self, user: str = "", password: str = "") -> Optional[Connection]:
        """
        从连接池获取连接
        
        Args:
            user: SAP 用户名（可选）
            password: SAP 密码（可选）
            
        Returns:
            RFC 连接对象，如果失败返回 None
        """
        with self._lock:
            # 清理超时连接
            now = datetime.now()
            self._pool = [
                (conn, last_used) 
                for conn, last_used in self._pool 
                if (now - last_used).total_seconds() < self.idle_timeout
            ]
            
            # 尝试复用现有连接
            if self._pool:
                conn, _ = self._pool.pop()
                if self._is_healthy(conn):
                    self._in_use.add(id(conn))
                    return conn
                else:
                    # 连接不健康，关闭
                    try:
                        conn.close()
                    except Exception:
                        pass
            
            # 创建新连接
            if len(self._in_use) < self.max_connections:
                # 设置环境变量
                old_user = os.environ.get("SAP_USER", "")
                old_pass = os.environ.get("SAP_PASSWORD", "")
                
                if user:
                    os.environ["SAP_USER"] = user
                if password:
                    os.environ["SAP_PASSWORD"] = password
                
                conn = self._create_connection()
                
                # 恢复环境变量
                if user:
                    os.environ["SAP_USER"] = old_user
                if password:
                    os.environ["SAP_PASSWORD"] = old_pass
                
                if conn:
                    self._in_use.add(id(conn))
                    return conn
            
            print(f"连接池已满（{len(self._in_use)}/{self.max_connections}）")
            return None
    
    def release_connection(self, conn: Connection) -> None:
        """
        释放连接回连接池
        
        Args:
            conn: RFC 连接对象
        """
        if conn is None:
            return
        
        conn_id = id(conn)
        
        with self._lock:
            if conn_id in self._in_use:
                self._in_use.remove(conn_id)
                
                if self._is_healthy(conn):
                    self._pool.append((conn, datetime.now()))
                else:
                    try:
                        conn.close()
                    except Exception:
                        pass
    
    def close_all(self) -> None:
        """关闭所有连接"""
        with self._lock:
            for conn, _ in self._pool:
                try:
                    conn.close()
                except Exception:
                    pass
            
            self._pool.clear()
            self._in_use.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        with self._lock:
            return {
                "max_connections": self.max_connections,
                "idle_connections": len(self._pool),
                "in_use_connections": len(self._in_use),
                "total_connections": len(self._pool) + len(self._in_use),
                "created_at": self._created_at.isoformat(),
                "idle_timeout": self.idle_timeout
            }
    
    def health_check(self) -> int:
        """
        健康检查，清理不健康的连接
        
        Returns:
            清理的连接数
        """
        cleaned = 0
        with self._lock:
            healthy_pool = []
            for conn, last_used in self._pool:
                if self._is_healthy(conn):
                    healthy_pool.append((conn, last_used))
                else:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    cleaned += 1
            self._pool = healthy_pool
        return cleaned


# 全局连接池实例
_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def get_pool(max_connections: int = 5, idle_timeout: int = 300) -> ConnectionPool:
    """获取全局连接池实例"""
    global _pool
    
    with _pool_lock:
        if _pool is None:
            # 加载性能配置
            perf_config = {}
            if os.path.exists(PERFORMANCE_FILE):
                try:
                    with open(PERFORMANCE_FILE, "r") as f:
                        perf_config = json.load(f)
                except Exception:
                    pass
            
            pool_config = perf_config.get("connection_pool", {})
            max_conn = pool_config.get("max_connections", max_connections)
            idle_to = pool_config.get("idle_timeout", idle_timeout)
            
            _pool = ConnectionPool(max_connections=max_conn, idle_timeout=idle_to)
        
        return _pool


def get_connection(user: str = "", password: str = "") -> Optional[Connection]:
    """从全局连接池获取连接"""
    pool = get_pool()
    return pool.get_connection(user=user, password=password)


def release_connection(conn: Connection) -> None:
    """释放连接回全局连接池"""
    pool = get_pool()
    pool.release_connection(conn)


def close_pool() -> None:
    """关闭全局连接池"""
    global _pool
    with _pool_lock:
        if _pool:
            _pool.close_all()
            _pool = None


def get_pool_stats() -> Dict[str, Any]:
    """获取连接池统计"""
    pool = get_pool()
    return pool.get_stats()


# 测试代码
if __name__ == "__main__":
    print("=== 连接池测试 ===")
    
    pool = get_pool()
    print(f"连接池已创建：{pool.get_stats()}")
    
    # 测试获取连接
    print("\n测试获取连接...")
    conn = get_connection()
    if conn:
        print("✓ 连接获取成功")
        print(f"连接池状态：{pool.get_stats()}")
        
        # 测试 RFC_PING
        try:
            result = conn.ping()
            print(f"✓ RFC_PING: {result}")
        except Exception as e:
            print(f"✗ RFC_PING 失败：{e}")
        
        # 释放连接
        release_connection(conn)
        print(f"连接已释放：{pool.get_stats()}")
    else:
        print("✗ 连接获取失败")
    
    # 关闭连接池
    close_pool()
    print(f"\n连接池已关闭：{pool.get_stats()}")
