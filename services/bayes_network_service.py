from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger("goodsleep_api.bayes_net")


class BayesNetworkService:
    """
    固定拓扑贝叶斯网络
    节点：
        H: 睡眠环境风险 (True=风险)
        T: 温度 [low, normal]
        RH: 湿度 [high, normal]
        M: 霉斑水渍 [yes, no]
        C: 杂乱 [yes, no]
        E: 电子设备 [yes, no]
        V: 通风 [poor, good]
    边：
        H → T, H → RH, H → M, H → C, H → E, H → V
        RH → M
    """
    def __init__(self):
        # CPT
        self.p_h = {True: 0.1, False: 0.9}

        self.p_t_given_h = {
            True: {"low": 0.55, "normal": 0.45},
            False: {"low": 0.15, "normal": 0.85},
        }
        self.p_rh_given_h = {
            True: {"high": 0.60, "normal": 0.40},
            False: {"high": 0.12, "normal": 0.88},
        }
        # P(M | H, RH)
        self.p_m_given_h_rh = {
            (True, "high"): {"yes": 0.88, "no": 0.12},
            (True, "normal"): {"yes": 0.38, "no": 0.62},
            (False, "high"): {"yes": 0.15, "no": 0.85},
            (False, "normal"): {"yes": 0.02, "no": 0.98},
        }

        self.p_c_given_h = {
            True: {"yes": 0.65, "no": 0.35},
            False: {"yes": 0.20, "no": 0.80},
        }
        self.p_e_given_h = {
            True: {"yes": 0.70, "no": 0.30},
            False: {"yes": 0.35, "no": 0.65},
        }
        self.p_v_given_h = {
            True: {"poor": 0.68, "good": 0.32},
            False: {"poor": 0.18, "good": 0.82},
        }

    def run(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        evidence: {"T":"low", "RH":"high", "M":"yes", "C":"yes", "E":"yes", "V":"good"}
        求 P(H=True | evidence)
        """
        trace: List[str] = []

        def joint_prob(h_val: bool):
            p = self.p_h[h_val]
            # T
            if "T" in evidence:
                p *= self.p_t_given_h[h_val][evidence["T"]]
            # RH
            if "RH" in evidence:
                p *= self.p_rh_given_h[h_val][evidence["RH"]]
            # M，依赖 H + RH
            if "M" in evidence:
                rh_val = evidence["RH"]
                p *= self.p_m_given_h_rh[(h_val, rh_val)][evidence["M"]]
            # C
            if "C" in evidence:
                p *= self.p_c_given_h[h_val][evidence["C"]]
            # E
            if "E" in evidence:
                p *= self.p_e_given_h[h_val][evidence["E"]]
            # V
            if "V" in evidence:
                p *= self.p_v_given_h[h_val][evidence["V"]]
            return p

        p_h_true = joint_prob(True)
        p_h_false = joint_prob(False)
        total = p_h_true + p_h_false
        posterior = p_h_true / total if total > 1e-9 else 0.0

        trace.append(f"P(H=True)原始联合={p_h_true:.6f}, P(H=False)原始联合={p_h_false:.6f}")
        trace.append(f"后验 P(H=True | E) = {posterior:.4f}")
        logger.info(f"BN trace: {trace}")
        return {
            "posterior": round(posterior, 4),
            "trace": trace
        }


# ---------------- 本地调试入口 ----------------
if __name__ == "__main__":
    bn = BayesNetworkService()
    # case1：温度低 + 湿度高 + 看见霉斑 + 杂乱 + 电子设备 + 通风良好
    case1 = {
        "T": "low",
        "RH": "high",
        "M": "yes",
        "C": "yes",
        "E": "yes",
        "V": "good"
    }
    res1 = bn.run(case1)
    print("=== Case1 温低+高湿+霉斑+杂乱+电子设备 ===")
    print(res1)

    # case2：只有温度低，其他正常
    case2 = {
        "T": "low",
        "RH": "normal",
        "M": "no",
        "C": "no",
        "E": "no",
        "V": "good"
    }
    res2 = bn.run(case2)
    print("\n=== Case2 仅温度偏低 ===")
    print(res2)

    # case3：高湿+霉斑，温度正常
    case3 = {
        "T": "normal",
        "RH": "high",
        "M": "yes",
        "C": "no",
        "E": "no",
        "V": "good"
    }
    res3 = bn.run(case3)
    print("\n=== Case3 高湿+霉斑，温度正常 ===")
    print(res3)
