from typing import Dict, List, Any
from .bayes_network_service import BayesNetworkService
from services.log_service import logger

class SleepEvalBayesService:
    def __init__(self):
        self.bn_service = BayesNetworkService()
        # 兜底开关
        self.enable_mold_safeguard = True

    def _encode_evidence(self, temperature: float, humidity: float, vision_obs: Dict[str, Any]) -> Dict[str, str]:
        """
        原始业务字段 → BN离散观测编码
        T: low / normal
        RH: high / normal
        M: yes / no
        C: yes / no
        E: yes / no
        V: poor / good
        """
        evidence = {}

        # 温度阈值：<20℃ 判定 low
        evidence["T"] = "low" if temperature < 20.0 else "normal"

        # 湿度阈值：>60% 判定 high
        evidence["RH"] = "high" if humidity > 60.0 else "normal"

        # 霉斑水渍
        mold_raw = vision_obs.get("mold_moisture", "未见")
        evidence["M"] = "yes" if mold_raw.strip().lower() not in ["未见", "none", ""] else "no"

        # 杂乱
        clutter_raw = vision_obs.get("clutter_level", "未见")
        evidence["C"] = "yes" if clutter_raw.strip().lower() not in ["未见", "none", ""] else "no"

        # 电子设备
        elec_raw = vision_obs.get("electronics", "未见")
        evidence["E"] = "yes" if elec_raw.strip().lower() not in ["未见", "none", ""] else "no"

        # 通风
        vent_raw = vision_obs.get("vent_condition", "未见")
        evidence["V"] = "poor" if vent_raw.strip().lower() not in ["未见", "none", ""] else "good"

        return evidence

    def _risk_mapping(self, posterior: float) -> Dict[str, str]:
        if posterior < 0.2:
            return {"riskLevel": "低风险", "riskClass": "risk-low"}
        elif posterior < 0.6:
            return {"riskLevel": "中风险", "riskClass": "risk-mid"}
        else:
            return {"riskLevel": "高风险", "riskClass": "risk-high"}

    def _get_desc_suggest(self, evidence: Dict[str, str]) -> tuple[List[str], List[str]]:
        desc = []
        suggest = []
        if evidence["T"] == "low":
            desc.append("温度低于舒适睡眠区间，偏凉会影响睡眠体感")
            suggest.append("调高室温至20–25℃")
        if evidence["RH"] == "high":
            desc.append("环境湿度偏高，属于霉菌容易滋生的区间")
            suggest.append("加强通风除湿，控制湿度在40–60%")
        if evidence["M"] == "yes":
            desc.append("墙面可见水渍痕迹，存在后续滋生霉菌的潜在条件")
            suggest.append("及时擦干水渍，保持墙面干燥，定期观察是否长出霉菌")
        if evidence["C"] == "yes":
            desc.append("卧室杂物较多，不利于空气流通、容易积尘")
            suggest.append("整理杂物，保持卧室通透整洁")
        if evidence["E"] == "yes":
            desc.append("卧室内放置电子设备，存在散热、光线干扰隐患")
            suggest.append("尽量不在床头附近摆放电子设备")
        if evidence["V"] == "poor":
            desc.append("通风条件差，室内污浊空气不易排出")
            suggest.append("定时开窗通风换气")
        if not desc:
            desc.append("当前卧室环境各项指标良好")
            suggest.append("继续维持现有环境习惯")
        return desc, suggest

    async def evaluate(self, temperature: float, humidity: float, vision_obs: Dict[str, Any]) -> Dict[str, Any]:
        evidence = self._encode_evidence(temperature, humidity, vision_obs)
        bn_res = self.bn_service.run(evidence)
        posterior = bn_res["posterior"]
        trace = bn_res["trace"]

        # 业务兜底：高湿+霉斑共存保底0.9
        if self.enable_mold_safeguard:
            if evidence.get("RH") == "high" and evidence.get("M") == "yes":
                if posterior < 0.9:
                    trace.append(f"业务兜底触发：高湿+霉斑共存，原始{posterior:.4f} → 修正为0.9000")
                    posterior = 0.9

        risk_info = self._risk_mapping(posterior)
        desc_items, suggest_items = self._get_desc_suggest(evidence)

        return {
            "riskLevel": risk_info["riskLevel"],
            "riskClass": risk_info["riskClass"],
            "posterior": posterior,
            "trace": trace,
            "desc_items": desc_items,
            "suggest_items": suggest_items,
            "evidence_count": len([v for v in evidence.values() if v not in ["normal", "no", "good"]])
        }