"""
OpenAI Agents基础组件
提供与OpenAI GPT模型交互的代理基础框架
"""

class Agent:
    """基础Agent类，其他所有专业Agent继承自此类"""
    
    def __init__(self, name: str, handoff_description: str, instructions: str, model: str):
        self.name = name
        self.handoff_description = handoff_description
        self.instructions = instructions
        self.model = model
