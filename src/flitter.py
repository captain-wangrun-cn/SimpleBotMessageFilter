import utils
from logger import logger

rules = {}
bypass_data = {}

def is_rule_pass(keyword: str, data: str, rule: str) -> bool:
    logger.debug(f"检查规则,关键字: {keyword},数据: {data},规则: {rule}")

    if rule == "contains":
        return keyword in data
    elif rule == "not_contains":
        return keyword not in data
    elif rule == "starts_with":
        return data.startswith(keyword)
    elif rule == "ends_with":
        return data.endswith(keyword)
    elif rule == "equals":
        return keyword == data
    elif rule == "not_equals":
        return keyword != data
    else:
        return False

async def check_message(message: dict) -> bool:
    user_id = str(message.get('user_id', ''))
    raw_message = message.get('raw_message', '')
    main_match = False

    for rule in rules:
        keyword = rule.get('keyword', '')
        pass_rule = rule.get('rule', "contains")
        bypass_config_data = rule.get('bypass', {})
        bypass_enabled = bypass_config_data.get('enable', False)
        bypass_time = 60
        bypass_rule_pass = False

        # 检查暂行机制
        if bypass_enabled:
            # 启用了暂行机制
            bypass_list = bypass_config_data.get('data', [])
            for bypass in bypass_list:
                bypass_keyword = bypass.get('keyword', '')
                bypass_pass_rule = bypass.get('rule', "contains")
                _bypass_time = bypass.get('time', 60)
                if is_rule_pass(bypass_keyword, raw_message, bypass_pass_rule):
                    bypass_rule_pass = True

                if user_id in bypass_data:
                    # 且已有暂行数据
                    if bypass_data[user_id] > utils.get_time_stamp():
                        # 数据还在有效期内,直接放行
                        logger.debug("符合暂行条件,且有暂行数据,放行")
                        bypass_time = _bypass_time
                        main_match = True
                    else:
                        # 数据已过期,删除暂行数据
                        del bypass_data[user_id]
                        logger.debug("暂行数据已过期,删除")
                    logger.debug("不符合暂行条件,且没有暂行数据")

                logger.debug("暂行不通过,开始检查主规则")
        else:
            logger.debug("未开启暂行")

        if is_rule_pass(keyword, raw_message, pass_rule):
            # 主规则通过
            main_match = True
            logger.debug("主规则通过")
                
        if main_match:
            # 规则通过
            if bypass_enabled and bypass_rule_pass:
                # 启用了暂行机制,并且符合条件
                bypass_data[user_id] = utils.get_time_stamp() + bypass_time
            
            
    return main_match
