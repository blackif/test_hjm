#!/usr/bin/env python3
"""
sap_service.py
SAP HTTP 服务接口

功能:
- 提供 RESTful API 供外部调用
- 支持连接复用（session_id）
- 批量操作优化
- 健康检查端点

依赖:
pip install fastapi uvicorn
"""

import os
import sys
import json
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from fastapi import FastAPI, HTTPException, Header
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("错误：需要安装 FastAPI 和 uvicorn")
    print("运行：pip install --break-system-packages fastapi uvicorn")
    sys.exit(1)

# 导入连接池
from connection_pool import get_connection, release_connection, get_pool_stats, close_pool

# 初始化 FastAPI 应用
app = FastAPI(
    title="SAP Agent Service",
    description="SAP RFC 操作 HTTP 接口",
    version="1.0.0"
)

# 会话存储
sessions: Dict[str, Dict] = {}
SESSION_TIMEOUT = 3600  # 会话超时时间（秒）


# ─────────────────────────────────────────────────
# 中间件
# ─────────────────────────────────────────────────

@app.middleware("http")
async def cleanup_sessions(request, call_next):
    """清理过期会话"""
    now = time.time()
    expired = [
        sid for sid, data in sessions.items()
        if now - data.get("created_at", 0) > SESSION_TIMEOUT
    ]
    for sid in expired:
        del sessions[sid]
    
    response = await call_next(request)
    return response


# ─────────────────────────────────────────────────
# 健康检查
# ─────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "sessions_active": len(sessions),
        "pool_stats": get_pool_stats()
    }


@app.get("/stats")
async def get_stats():
    """获取服务统计"""
    return {
        "sessions": {
            "active": len(sessions),
            "timeout": SESSION_TIMEOUT
        },
        "pool": get_pool_stats()
    }


# ─────────────────────────────────────────────────
# 连接管理
# ─────────────────────────────────────────────────

@app.post("/connect")
async def connect(
    user: str = "",
    password: str = "",
    x_session_id: Optional[str] = Header(None)
):
    """
    建立 SAP 连接
    
    Args:
        user: SAP 用户名
        password: SAP 密码
        x_session_id: 可选的会话 ID（用于复用连接）
    
    Returns:
        session_id: 会话 ID
    """
    try:
        # 获取连接
        conn = get_connection(user=user, password=password)
        
        if not conn:
            raise HTTPException(status_code=500, detail="无法建立 SAP 连接")
        
        # 创建会话
        session_id = x_session_id or str(uuid.uuid4())
        sessions[session_id] = {
            "created_at": time.time(),
            "last_used": time.time(),
            "user": user,
            "connection": conn
        }
        
        # 测试连接
        try:
            conn.ping()
            connected = True
        except Exception:
            connected = False
        
        return {
            "session_id": session_id,
            "connected": connected,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/disconnect")
async def disconnect(
    x_session_id: str = Header(..., description="会话 ID")
):
    """
    断开 SAP 连接
    
    Args:
        x_session_id: 会话 ID
    """
    if x_session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        session = sessions[x_session_id]
        conn = session.get("connection")
        
        if conn:
            release_connection(conn)
        
        del sessions[x_session_id]
        
        return {
            "status": "disconnected",
            "session_id": x_session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────
# RFC 调用
# ─────────────────────────────────────────────────

@app.post("/call")
async def call_rfc(
    function_name: str,
    parameters: Dict[str, Any] = {},
    x_session_id: str = Header(..., description="会话 ID")
):
    """
    调用 RFC 函数
    
    Args:
        function_name: RFC 函数名
        parameters: 函数参数
        x_session_id: 会话 ID
    """
    if x_session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = sessions[x_session_id]
    session["last_used"] = time.time()
    conn = session.get("connection")
    
    if not conn:
        raise HTTPException(status_code=500, detail="连接不可用")
    
    try:
        result = conn.call(function_name, **parameters)
        
        # 转换结果为 JSON 可序列化格式
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, bytes):
                return obj.decode("utf-8", errors="replace")
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [serialize(v) for v in obj]
            else:
                return obj
        
        return {
            "success": True,
            "result": serialize(result),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ─────────────────────────────────────────────────
# 表查询（优化版）
# ─────────────────────────────────────────────────

@app.post("/read_table")
async def read_table(
    table_name: str,
    fields: List[str] = [],
    options: List[str] = [],
    rowcount: int = 100,
    delimiter: str = "|",
    x_session_id: str = Header(..., description="会话 ID")
):
    """
    批量查询 SAP 表
    
    Args:
        table_name: 表名
        fields: 字段列表
        options: 查询条件（WHERE 子句）
        rowcount: 最大行数
        delimiter: 分隔符
        x_session_id: 会话 ID
    """
    if x_session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = sessions[x_session_id]
    session["last_used"] = time.time()
    conn = session.get("connection")
    
    if not conn:
        raise HTTPException(status_code=500, detail="连接不可用")
    
    try:
        # 构建字段参数
        fields_param = [{"FIELDNAME": f} for f in fields] if fields else []
        
        # 构建选项参数
        options_param = [{"TEXT": opt} for opt in options] if options else []
        
        # 调用 RFC_READ_TABLE
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE=table_name,
            DELIMITER=delimiter,
            ROWCOUNT=rowcount,
            FIELDS=fields_param,
            OPTIONS=options_param
        )
        
        # 解析结果
        data = []
        if result.get("DATA"):
            field_names = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
            for row in result["DATA"]:
                values = row["WA"].split(delimiter)
                row_data = {}
                for i, field in enumerate(field_names):
                    row_data[field] = values[i] if i < len(values) else ""
                data.append(row_data)
        
        return {
            "success": True,
            "table": table_name,
            "rowcount": len(data),
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ─────────────────────────────────────────────────
# 批量操作
# ─────────────────────────────────────────────────

@app.post("/batch")
async def batch_operations(
    operations: List[Dict[str, Any]],
    x_session_id: str = Header(..., description="会话 ID")
):
    """
    批量执行操作
    
    Args:
        operations: 操作列表，每个操作包含:
            - type: "call" | "read_table"
            - params: 操作参数
        x_session_id: 会话 ID
    """
    if x_session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = sessions[x_session_id]
    session["last_used"] = time.time()
    conn = session.get("connection")
    
    if not conn:
        raise HTTPException(status_code=500, detail="连接不可用")
    
    results = []
    start_time = time.time()
    
    for i, op in enumerate(operations):
        try:
            op_type = op.get("type", "")
            params = op.get("params", {})
            
            if op_type == "call":
                func_name = params.get("function_name", "")
                func_params = params.get("parameters", {})
                result = conn.call(func_name, **func_params)
                results.append({
                    "index": i,
                    "success": True,
                    "result": result
                })
            elif op_type == "read_table":
                table_name = params.get("table_name", "")
                rowcount = params.get("rowcount", 100)
                fields = params.get("fields", [])
                result = conn.call(
                    "RFC_READ_TABLE",
                    QUERY_TABLE=table_name,
                    ROWCOUNT=rowcount,
                    FIELDS=[{"FIELDNAME": f} for f in fields]
                )
                results.append({
                    "index": i,
                    "success": True,
                    "result": result
                })
            else:
                results.append({
                    "index": i,
                    "success": False,
                    "error": f"未知操作类型：{op_type}"
                })
                
        except Exception as e:
            results.append({
                "index": i,
                "success": False,
                "error": str(e)
            })
    
    elapsed = time.time() - start_time
    
    return {
        "total": len(operations),
        "success": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
        "elapsed_seconds": elapsed,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


# ─────────────────────────────────────────────────
# 服务关闭
# ─────────────────────────────────────────────────

@app.post("/shutdown")
async def shutdown():
    """关闭服务"""
    # 关闭所有会话
    for session in sessions.values():
        conn = session.get("connection")
        if conn:
            release_connection(conn)
    sessions.clear()
    
    # 关闭连接池
    close_pool()
    
    return {
        "status": "shutting_down",
        "sessions_closed": len(sessions),
        "timestamp": datetime.now().isoformat()
    }


# ─────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────

def main():
    """启动服务"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SAP Agent HTTP Service")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8765, help="监听端口")
    parser.add_argument("--reload", action="store_true", help="开发模式（自动重载）")
    
    args = parser.parse_args()
    
    print(f"启动 SAP Agent 服务...")
    print(f"  地址：http://{args.host}:{args.port}")
    print(f"  健康检查：http://{args.host}:{args.port}/health")
    print(f"  统计信息：http://{args.host}:{args.port}/stats")
    print("")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
