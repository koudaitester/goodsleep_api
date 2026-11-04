# services/sleep_env_service.py
from schemas.sleep import SleepEnvEvalReq, SleepEnvEvalResp
from services.log_service import logger
from fastapi import HTTPException
from utils.common import bayes_two_pair

# ========== 湿度-霉菌 贝叶斯配置（写在RULES上方） ==========
BAYES_RH_MOLD_CONF = {
        "prior_h": 0.10,
        "p_x_given_h": {          # P(RH|风险H)
            "high": 0.60,
            "normal": 0.30
        },
        "p_x_given_not_h": {      # P(RH|无风险¬H)
            "high": 0.20,
            "normal": 0.75
        },
        "p_y_given_h_x": {        # P(M | H, RH)
            ("high", "yes"): 0.90,
            ("high", "no"): 0.10,
            ("normal", "yes"): 0.40,
            ("normal", "no"): 0.60,
        },
        "p_y_given_not_h_x": {    # P(M | ¬H, RH)
            ("high", "yes"): 0.30,
            ("high", "no"): 0.70,
            ("normal", "yes"): 0.08,
            ("normal", "no"): 0.92,
        },
        "scale": 0.22
    }

RULES = [
    {
        "id": "temp_high",
        "test": lambda v, e: e.temperature is not None and e.temperature > 25,
        "desc": "温度高于舒适睡眠区间，高温更容易造成入睡困难",
        "suggest": "降低室温至20–25℃",
        "delta": 0.20
    },
    {
        "id": "temp_low",
        "test": lambda v, e: e.temperature is not None and e.temperature < 20,
        "desc": "温度低于舒适睡眠区间，偏凉会影响睡眠体感",
        "suggest": "调高室温至20–25℃",
        "delta": 0.10
    },
    # {
    #     "id": "hum_high",
    #     "test": lambda v, e: e.humidity is not None and e.humidity > 55,
    #     "desc": "湿度过高，利于霉菌滋生",
    #     "suggest": "开启除湿，湿度控制在45–55%区间",
    #     "delta": 0.15
    # },
    {
        "id": "hum_low",
        "test": lambda v, e: e.humidity is not None and e.humidity < 45,
        "desc": "湿度偏低，容易咽干不适",
        "suggest": "适度加湿，湿度维持45–55%区间",
        "delta": 0.10
    },
    {
        "id": "stain_only",
        "test": lambda v, e: v and ("water stain" in v.mold_moisture or "water stain" in v.wall_ceiling) and not ("mold" in v.mold_moisture or "damp" in v.mold_moisture),
        "desc": "墙面可见水渍痕迹，存在后续滋生霉菌的潜在条件",
        "suggest": "及时擦干水渍，保持墙面干燥，定期观察是否长出霉菌",
        "delta": 0.10
    },
    # {
    #     "id": "mold_exist",
    #     "test": lambda v, e: v and ("mold" in v.mold_moisture or "damp" in v.mold_moisture),
    #     "desc": "墙面识别出霉菌/潮湿痕迹，存在霉菌暴露风险",
    #     "suggest": "尽快清理霉菌，排查渗水源头，加强通风除湿",
    #     "delta": 0.12
    # },
    # {
    #     "id": "mold_grow_risk",
    #     "test": lambda v, e: v and ("mold" in v.mold_moisture or "damp" in v.mold_moisture) and e.humidity is not None and e.humidity > 55,
    #     "desc": "存在霉菌痕迹且湿度过高，环境适合霉菌孢子持续增殖",
    #     "suggest": "立即开启除湿设备，把湿度降到55%以下，配合开窗通风",
    #     "delta": 0.20
    # },
    {
        "id": "clutter",
        "test": lambda v, e: v and ("disarray" in v.clutter_level or "scattered" in v.clutter_level or "cluttered" in v.clutter_level),
        "desc": "床边物品杂乱，容易造成心理干扰",
        "suggest": "收纳床边散落物品，简化卧室视觉负担",
        "delta": 0.05
    },
    {
        "id": "bedding_rumpled",
        "test": lambda v, e: v and v.bedding_status == "rumpled",
        "desc": "床品褶皱凌乱，不利于放松入睡",
        "suggest": "整理床品，维持整洁的睡眠环境",
        "delta": 0.08
    },
    {
        "id": "vent_closed",
        "test": lambda v, e: v and ("window closed" in v.vent_condition or "window is closed" in v.vent_condition),
        "desc": "窗户关闭，室内空气流通偏弱",
        "suggest": "定时开窗换气，改善室内空气质量",
        "delta": 0.12
    },
    {
        "id": "light_leak",
        "test": lambda v, e: v and "light leakage" in v.window_curtain,
        "desc": "窗帘遮光不足，光线容易干扰睡眠",
        "suggest": "更换加厚遮光窗帘，减少夜间光线侵入",
        "delta": 0.12
    },
    {
        "id": "bed_blocked",
        "test": lambda v, e: v and v.bed_occlusion != "未见",
        "desc": "床体存在遮挡，不利于散热与空气流通",
        "suggest": "移开遮挡物，保证床周边通畅",
        "delta": 0.16
    },
    {
        "id": "dust",
        "test": lambda v, e: v and v.dust_accumulation != "未见",
        "desc": "可见灰尘堆积，容易刺激呼吸道",
        "suggest": "定期除尘，降低呼吸道刺激风险",
        "delta": 0.10
    },
    {
        "id": "electronics",
        "test": lambda v, e: v and v.electronics in ("phone lamp", "phone", "lamp"),
        "desc": "卧室存在电子设备，可能带来光照与干扰",
        "suggest": "睡前远离手机，减少蓝光刺激",
        "delta": 0.11
    },
    {
        "id": "mold_risk_high",
        "test": lambda v, e: e.mold_risk_level in ("中等", "高"),
        "desc": lambda v, e: f"霉菌评估风险：{e.mold_risk_level}",
        "suggest": "重点排查潮湿源，除霉通风",
        "delta": 0.25
    },
    {
        "id": "sleep_late_00",
        "test": lambda v, e: e.sleep_start_hour == 0,
        "desc": "零点入睡，偏离推荐睡眠时段",
        "suggest": "尽量提前至23点前入睡",
        "delta": 0.08
    },
    {
        "id": "sleep_late_01",
        "test": lambda v, e: e.sleep_start_hour == 1,
        "desc": "凌晨1点入睡，入睡时间偏晚",
        "suggest": "调整作息，尽量23点前上床休息",
        "delta": 0.12
    },
    {
        "id": "sleep_late_02",
        "test": lambda v, e: e.sleep_start_hour == 2,
        "desc": "凌晨2点入睡，作息严重延后",
        "suggest": "逐步提前入睡时间，修复睡眠节律",
        "delta": 0.16
    },
    {
        "id": "sleep_late_03",
        "test": lambda v, e: e.sleep_start_hour == 3,
        "desc": "凌晨3点入睡，节律紊乱风险高",
        "suggest": "尽快调整作息，避免长期熬夜",
        "delta": 0.20
    }

]

GRADE_MAP = [
    {"min_p": 0.6, "level": "高风险", "cls": "risk-high"},
    {"min_p": 0.4, "level": "中等风险", "cls": "risk-medium"},
    {"min_p": 0, "level": "低风险", "cls": "risk-low"},
]

def filter_conflict_rules(hit_rule_ids: list[str]) -> list[str]:
    hit_set = set(hit_rule_ids)
    out = []
    for rid in hit_rule_ids:
        # 有水渍并且命中任意霉菌规则，去掉水渍
        if rid == "stain_only" and ("mold_exist" in hit_set or "mold_grow_risk" in hit_set):
            continue
        # 同时命中mold_exist 和 mold_grow_risk：保留mold_grow_risk，丢掉mold_exist
        if rid == "mold_exist" and "mold_grow_risk" in hit_set:
            continue
        out.append(rid)
    logger.info(f"[SleepEval] filter_conflict_rules: input={hit_rule_ids}, output={out}")
    return out

class SleepEnvService:
    async def evaluate(self, req: SleepEnvEvalReq) -> SleepEnvEvalResp:
        vision = req.vision_obs
        logger.info(f"[SleepEval] temp={req.temperature}, hum={req.humidity}, sleep_start_hour={req.sleep_start_hour}, mold={req.mold_risk_level}")
        if vision:
            logger.info(f"[SleepEval] vision_obs={vision.model_dump(by_alias=True)}")

        hit_ids = []
        desc_items = []
        suggest_items = []
        trace = []
        posterior = 0.0

        for rule in RULES:
            if rule["test"](vision, req):
                hit_ids.append(rule["id"])

        # 调用外部公共去重函数
        hit_ids = filter_conflict_rules(hit_ids)

        rule_map = {r["id"]: r for r in RULES}

        for rid in hit_ids:
            rule = rule_map[rid]
            d = rule["desc"](vision, req) if callable(rule["desc"]) else rule["desc"]
            s = rule["suggest"]
            desc_items.append(d)
            suggest_items.append(s)
            trace.append(f"rule:{rid} +{rule['delta']}")
            posterior += rule["delta"]
                
        logger.info(f"[SleepEval] hit_ids={hit_ids}, desc_items={desc_items}, suggest_items={suggest_items}, posterior={posterior}")

        # 湿度-霉菌 贝叶斯计算
        if req.humidity is not None and req.humidity > 55:
            rh_state = "high"
        else:
            rh_state = "normal"
        # 编码霉菌状态
        m_state = "no"
        if vision and vision.mold_moisture:
            if "mold" in vision.mold_moisture or "damp" in vision.mold_moisture:
                m_state = "yes"
            else:
                m_state = "no"

        post_rh_mold, add_rh_mold = bayes_two_pair(
            prior_h=BAYES_RH_MOLD_CONF["prior_h"],
            p_x_given_h=BAYES_RH_MOLD_CONF["p_x_given_h"],
            p_y_given_h_x=BAYES_RH_MOLD_CONF["p_y_given_h_x"],
            x_state=rh_state,
            y_state=m_state,
            p_x_given_not_h=BAYES_RH_MOLD_CONF["p_x_given_not_h"],
            p_y_given_not_h_x=BAYES_RH_MOLD_CONF["p_y_given_not_h_x"],
            scale=BAYES_RH_MOLD_CONF["scale"]
        )
        trace.append(f"bayes:rh-mold | post={post_rh_mold:.4f} +{add_rh_mold:.4f}")
        posterior += add_rh_mold

        # 业务兜底：高湿+霉菌保底增量0.20
        if rh_state == "high" and m_state == "yes":
            if add_rh_mold < 0.20:
                trace.append(f"bayes:rh-mold safeguard, override +0.20")
                posterior -= add_rh_mold
                add_rh_mold = 0.20
                posterior += add_rh_mold

        posterior = min(posterior, 0.95)
        evidence_count = len(hit_ids) + 1

        riskLevel, riskClass = "低风险", "risk-low"
        # 根据后验概率匹配风险等级
        for g in GRADE_MAP:
            if posterior >= g["min_p"]:
                riskLevel, riskClass = g["level"], g["cls"]
                break

        desc_str = "；".join(desc_items) if desc_items else "综合评估结果：低风险"
        suggest_str = "；".join(suggest_items) if suggest_items else "卧室环境条件良好，保持现有通风与温湿度即可。"
        logger.info(f"[SleepEval] riskLevel={riskLevel}, riskClass={riskClass}, posterior={posterior}, trace={trace}, evidence_count={evidence_count}")
        raw_text = vision.model_dump().get("__raw_text__", "") if vision else ""
        space_type = vision.model_dump().get("space_type", "") if vision else ""
        # 如果提供了视觉分析结果，但原始文本中没有提到“bedroom”，则提示用户提供正确的卧室图片
        if space_type and "卧室" != space_type.lower():
            logger.warning(f"[sleep_env_service] Detected space_type is not bedroom: {space_type}. Please provide a bedroom image for evaluation.")
            raise HTTPException(status_code=400, detail="识别非卧室场景，请上传卧室照片进行评估")
        extraNote = f"{raw_text}" if raw_text else "单环境评估，无异常风险"
        
        return SleepEnvEvalResp(
            riskLevel=riskLevel,
            riskClass=riskClass,
            desc=desc_str,
            suggest=suggest_str,
            extraNote=extraNote,
            bayes={
                "posterior": round(posterior, 2),
                "trace": trace,
                "evidence_count": evidence_count
            }
        )


sleep_env_service = SleepEnvService()





