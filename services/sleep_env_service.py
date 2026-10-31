from schemas.sleep import SleepEnvEvalReq, SleepEnvEvalResp

class SleepEnvService:
    @staticmethod
    def evaluate(req: SleepEnvEvalReq) -> SleepEnvEvalResp:
        # 先返回mock数据，链路通了再塞打分+贝叶斯逻辑
        return SleepEnvEvalResp(
            riskLevel="低风险",
            riskClass="risk-low",
            desc="综合评估结果：低风险",
            suggest="卧室环境条件良好，保持现有通风与温湿度即可。",
            extraNote="单环境评估，无异常风险",
            bayes={"posterior":0.0, "trace":[], "evidence_count":0}
        )
