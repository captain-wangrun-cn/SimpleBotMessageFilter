import utils
from logger import logger
from collections import defaultdict
import re

filter_private = True
rules = {}
bypass_data = {}
rule_cache = defaultdict(dict)

# 预编译常用正则表达式
rule_patterns = {
    "contains": re.compile(r"{keyword}"),
    "starts_with": re.compile(r"^{keyword}"),
    "ends_with": re.compile(r"{keyword}$")
}

def is_rule_pass(keyword: str, data: str, rule: str) -> bool:
    # 检查缓存
    cache_key = f"{keyword}_{rule}"
    if data in rule_cache[cache_key]:
        return rule_cache[cache_key][data]
        
    logger.debug(f"检查规则,关键字: {keyword},数据: {data},规则: {rule}")

    # 使用预编译的正则表达式
    if rule in rule_patterns:
        pattern = rule_patterns[rule].format(keyword=re.escape(keyword))
        result = bool(pattern.search(data))
    elif rule == "equals":
        result = keyword == data
    elif rule == "not_equals":
        result = keyword != data
    else:
        result = False
    
    # 更新缓存
    rule_cache[cache_key][data] = result
    return result

async def check_message(message: dict) -> bool:
    user_id = str(message.get('user_id', ''))
    raw_message = message.get('raw_message', '')
    
    # 快速检查私聊消息
    if not filter_private and message.get('sub_type') == 'friend':
        return True
    
    # 预处理消息内容
    message_lower = raw_message.lower()
    
    for rule in rules:
        keyword = rule.get('keyword', '').lower()
        pass_rule = rule.get('rule', "contains")
        
        # 先检查主规则
        if not is_rule_pass(keyword, message_lower, pass_rule):
            continue
            
        # 检查暂行机制
        bypass_config_data = rule.get('bypass', {})
        if bypass_config_data.get('enable', False):
            bypass_list = bypass_config_data.get('data', [])
            for bypass in bypass_list:
                bypass_keyword = bypass.get('keyword', '').lower()
                if is_rule_pass(bypass_keyword, message_lower, bypass.get('rule', "contains")):
                    return True
        
        return True
    
    return False
