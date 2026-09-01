# bad.py — 代码评审门禁反例：含多种评审坏味道
import os

DB_PASSWORD = "S3cr3tP@ssw0rd"          # CR-HARDCODED-SECRET (critical / blocking)


def process(user_id):
    # TODO 这里要重构一下            # CR-TODO-NO-TICKET (medium)
    print("debug")                      # CR-DEBUG-PRINT (low)
    query = "SELECT * FROM users WHERE id=" + user_id   # CR-SQL-CONCAT (high)
    return query


def giant():
    # pad 001
    # pad 002
    # pad 003
    # pad 004
    # pad 005
    # pad 006
    # pad 007
    # pad 008
    # pad 009
    # pad 010
    # pad 011
    # pad 012
    # pad 013
    # pad 014
    # pad 015
    # pad 016
    # pad 017
    # pad 018
    # pad 019
    # pad 020
    # pad 021
    # pad 022
    # pad 023
    # pad 024
    # pad 025
    # pad 026
    # pad 027
    # pad 028
    # pad 029
    # pad 030
    # pad 031
    # pad 032
    # pad 033
    # pad 034
    # pad 035
    # pad 036
    # pad 037
    # pad 038
    # pad 039
    # pad 040
    # pad 041
    # pad 042
    # pad 043
    # pad 044
    # pad 045
    # pad 046
    # pad 047
    # pad 048
    # pad 049
    # pad 050
    # pad 051
    # pad 052
    # pad 053
    # pad 054
    # pad 055
    # pad 056
    # pad 057
    # pad 058
    # pad 059
    # pad 060
    # pad 061
    # pad 062
    # pad 063
    # pad 064
    # pad 065
    # pad 066
    # pad 067
    # pad 068
    # pad 069
    # pad 070
    # pad 071
    # pad 072
    # pad 073
    # pad 074
    # pad 075
    # pad 076
    # pad 077
    # pad 078
    # pad 079
    # pad 080
    # pad 081
    # pad 082
    # pad 083
    # pad 084
    # pad 085
    # pad 086
    # pad 087
    # pad 088
    # pad 089
    # pad 090
    pass
