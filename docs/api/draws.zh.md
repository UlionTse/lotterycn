# draws — 开奖详情

官方开奖公告的完整字段：销售额、奖池、各奖级中奖注数与单注奖金、一等奖省级分布，输出三张 tidy 表并支持增量缓存。

::: lotterycn.draws
    options:
      members:
        - load_draw_detail
        - load_prize_results
        - load_first_prize_by_province
