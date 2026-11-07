"""engines/common：子平引擎族共享计算层（引擎无关）。

- l0_adapter：L0 Chart → 基础 rules view + 求值上下文（只映射，不重排盘）
- result：§70 通用 EngineResult（六组 facts 统一结构）
- facts_builder：engine 参数化 FactsBuilder（消费正式 Registry，输出 EngineResult）

五部引擎（ziping_zhenquan/ditiansui/qiongtong_baojian/sanming_tonghui/shenfeng_tongkao）
经此共享层复用 L0 映射与事实管线；yuhai_ziping 同样转发至此。
不属任何 Engine（不在 check_import_boundaries 的 ENGINE_MODULES），引擎可自由 import。
"""
