from typing import Dict

from constants import CHARACTER_TABLE_URL, STAGE_TABLE_URL
from core.function.update import updateData
from logger import writeLog


class MissionTemplate:
    def __init__(self, battle_data: Dict, player_data: Dict, battle_info: Dict,
                 mission_id: str, stage_id: str = None, extra: Dict = dict()):
        '''
        extra -> Dict: {
            apCost -> int
            goldCost -> int
            goldCostPlus -> int
            socialPoint -> int
            sendClue -> int
            upgradeCharExp -> int
            normalGachaCount -> int
            recoverCharBaseAp -> int
            deliveryOrder -> int
            manufactureItem -> int
            infoShareCount -> int
            gainIntimacyCount -> int
        }

        Usage:
            Init mission -> getattr(MissionTemplate(None, player_data, None, mission_id, None, None), template)(*param)
            Check progress -> getattr(MissionTemplate(battle_data, player_data, battle_info, missionId, stage_id, extra), template)(*param)
            Complete the mission -> getattr(MissionTemplate(None, player_data, None, missionId, None, None), "CompleteMission")({activityId: missionIds})
        '''
        self.battle_data = battle_data
        self.player_data = player_data
        self.battle_info = battle_info
        self.mission_id = mission_id
        self.stage_id = stage_id
        self.extra = extra

    def InitMission(self, target) -> Dict:
        self.player_data["mission"]["missions"]["ACTIVITY"].setdefault(self.mission_id, {
            "state": 2,
            "progress": [
                {
                    "target": target,
                    "value": 0
                }
            ]
        })
        return self.player_data

    def UpdateMission(self, value) -> None:
        self.player_data["mission"]["missions"]["ACTIVITY"][self.mission_id]["progress"][0]["value"] += value
        self.CheckMission()

    def CheckMission(self) -> Dict:
        value = self.player_data["mission"]["missions"]["ACTIVITY"][self.mission_id]["progress"][0]["value"]
        target = self.player_data["mission"]["missions"]["ACTIVITY"][self.mission_id]["progress"][0]["target"]
        if value >= target:
            self.player_data["mission"]["missions"]["ACTIVITY"][self.mission_id]["progress"][0]["value"] = target
        return self.player_data

    def CompleteMission(self, user_info) -> Dict:
        '''
        {activityId: missionIds} -> Dict[List]
        '''
        check_status = 0
        for activityId, missionIds in user_info.items():
            for mission_id in missionIds:
                if self.player_data["mission"]["missions"]["ACTIVITY"][mission_id]["state"] == 3:
                    check_status += 1
            if len(missionIds) == check_status:
                self.player_data["mission"]["missionGroups"][activityId] = 1
        self.player_data["mission"]["missions"]["ACTIVITY"][self.mission_id]["state"] = 3
        return self.player_data

    def ActivityCoinGain(self, *args) -> None:
        '''
        Type:
            0：《愚人号》活动期间，累计获得<n>个锈蚀的罗盘

        Param example:
            0 -> ["0","act17side","500","act17side_token_compass"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[2]))
            writeLog(f"\033[1;31mUnsupported templateType: {args}\033[0;0m", "error")

    def Act13sideCompleteDailyMission(self, *args) -> None:
        '''
        Type:
            0：完成每日事务<n>次

        Param example:
            0 -> ["0","5"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            writeLog(f"\033[1;31mUnsupported templateType: {args}\033[0;0m", "warning")  # TODO
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def Act20sideApprovalCar(self, *args) -> None:
        '''
        Type:
            0：在自走车友会中参与<n>次车友交流

        Param example:
            0 -> ["0","3"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            writeLog(f"\033[1;31mUnsupported templateType: {args}\033[0;0m", "warning")  # TODO
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def Act20sideConfirmExhiCar(self, *args) -> None:
        '''
        Type:
            0：在自走车友会中，完成1次外观设计并装配至少<n>个稀有度为蓝色或以上的装备

        Param example:
            0 -> ["0","durcar_gear_a_1_2;durcar_gear_a_2_2;durcar_gear_a_3_2;","6"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            writeLog(f"\033[1;31mUnsupported templateType: {args}\033[0;0m", "warning")  # TODO
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def Act20sideGainAccessories(self, *args) -> None:
        '''
        Type:
            0：累计收集<n>种装备

        Param example:
            0 -> ["0","durcar_gear_a_1_1;durcar_gear_a_1_2durcar_gear_a_2_1;","25"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[2]))
            writeLog(f"\033[1;31mUnsupported templateType: {args}\033[0;0m", "warning")  # TODO
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def Act20sidePassStageWithCar(self, *args) -> None:
        '''
        Type:
            0：装配至少<n>个自走车装备并<m>星通关<satge>

        Param example:
            0 -> ["0","3","act20side_s03","durcar_gear_a_1_1;durcar_gear_a_1_2;durcar_gear_a_2_1;","6"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for i in self.battle_data["battleData"]["stats"]["packedRuneDataList"]:
                    if i in args[3]:
                        count += 1
                if count >= int(args[4]):
                    self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def Act20sideSeekAccessories(self, *args) -> None:
        '''
        Type:
            0：在装备集换处中获取装备<n>次

        Param example:
            0 -> ["0","30"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            writeLog(f"\033[1;31mUnsupported templateType: {args}\033[0;0m", "warning")  # TODO
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def BuyShopItem(self, *args) -> None:
        '''
        Type:
            3：在信用商店中累计消费<n>点信用点

        Param example:
            3 -> ["0","1600"]
        '''
        if int(args[0]) == 3:
            self.InitMission(int(args[1]))
            if "socialPoint" in self.extra:
                self.UpdateMission(self.extra["socialPoint"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteAnyMulStage(self, *args) -> None:
        '''
        Type:
            0：通关多维合作<stage>

        Param example:
            0 -> ["0","act17d1_02_a","3","act17d1"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            if args[1] == self.stage_id and self.battle_data["completeState"] >= int(args[2]):
                self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteAnyStage(self, *args) -> None:
        '''
        Type:
            0：以<n>星评价完成<stage>

        Param example:
            0 -> ["0","act22side_06","3"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            if args[1] == self.stage_id and self.battle_data["completeState"] >= int(args[2]):
                self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteCampaign(self, *args) -> None:
        '''
        Type:
            1：任务期间累计在剿灭作战中击杀<n>个敌人

        Param example:
            1 -> ["1","1000"]
        '''
        if int(args[0]) == 1:
            self.InitMission(int(args[1]))
            if self.stage_id and self.battle_data["completeState"] >= 2:
                STAGE_TABLE = updateData(STAGE_TABLE_URL, True)
                if STAGE_TABLE["stages"][self.stage_id]["stageType"] == "CAMPAIGN":
                    self.UpdateMission(self.battle_data["killCnt"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteDailyStage(self, *args) -> None:
        '''
        Type:
            1：完成任意物资筹备中的关卡<n>次

        Param example:
            1 -> ["1","MATERIAL","8"]
        '''
        if int(args[0]) == 1:
            self.InitMission(int(args[2]))
            if self.stage_id and self.battle_data["completeState"] >= 2:
                STAGE_TABLE = updateData(STAGE_TABLE_URL, True)
                if STAGE_TABLE["stages"][self.stage_id]["stageType"] == "DAILY":
                    self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteInterlockStage(self, *args) -> None:
        '''
        Type:
            0：通关最终关卡FIN-TS时，驻守关卡<stage1>和<stage2>

        Param example:
            0 -> ["0","act1lock_c-01","act1lock_b-01^act1lock_b-03"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            writeLog(f"\033[1;31mUnsupported templateType: {args}\033[0;0m", "warning")  # TODO
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteMainStage(self, *args) -> None:
        '''
        Type:
            0：通关任意主线关卡20次，不包含0理智关卡

        Param example:
            0 -> ["0","2","20"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[2]))
            if self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                STAGE_TABLE = updateData(STAGE_TABLE_URL, True)
                if STAGE_TABLE["stages"][self.stage_id]["stageType"] == "MAIN" and STAGE_TABLE["stages"][self.stage_id]["apCost"] != 0:
                    self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteStage(self, *args) -> None:
        '''
        Type:
            0：<condition>我看到了三个游荡的巨人。看到了我们的山

        Param example:
            0 -> ["0","act11d0_s01#f#","1"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            writeLog(f"\033[1;31mUnsupported templateType: {args}\033[0;0m", "warning")  # TODO
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteStageAct(self, *args) -> None:
        '''
        Type:
            0：通关<stages><n>次,不含教学关
            1：通关<stage>

        Param example:
            0 -> ["0","act17side_01^act17side_02^act17side_03","85"]
            1 -> ["1","act15side_01","1","2"]
        '''

        if int(args[0]) == 0:
            self.InitMission(int(args[2]))
            for i in args[1].split("^"):
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    self.UpdateMission(1)
                    break
        elif int(args[0]) == 1:
            self.InitMission(int(args[2]))
            if args[1] == self.stage_id and self.battle_data["completeState"] >= int(args[3]):
                self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteStageCondition(self, *args) -> None:
        '''
        Type:
            0：通关<stage>，且使用<skills><n>次
            2：完成<stage>且至少使用<n>次<condition>
            3：以<n>星评价完成<stage>且不使用<condition>
            4：以<n>星评价完成<stage>且不升级任何<condition>
            5：<condition>而守在门前，却不过六人而已
            6：<condition>理当放弃所有的装置去战斗
            7：<condition>敌人始终没能碰触到那些发声的机器
            8：以<n>星评价完成<stage>，且击败<enemy>
            9：以<n>星评价完成<stage>，且<enemy>至多施放<m>次<skill>
            10：通关<stage>，且使用<team>干员击败<n>个<enemy><condition>
            11：通关<stage>，且在涨潮持续期间，至多<n>名潮汐中的地面干员撤退或被击倒
            12：<n>星通关<stage>,并且<chars>不被击败
            13：以<n>星评价完成<stage>，且部署非助战的<character>上阵
            14：<n>星通关<stage>，且屠谕者获得定向进化效果数量至少<m>种
            15：<n>星通关<stage>，且受溟痕影响过的干员最多<m>个
            16：通关<stage>，且部署<team>干员<n>次
            17：通关<stage>，且小队中编入至少<n>位标签为<tag>的干员（不包括固定阵容）

        Param example:
            0 -> ["0","2","act1bossrush_tm02","skchr_shotst_2^skchr_estell_2^skchr_cutter_1,"20"]
            2 -> ["2","2","act5d0_06","trap_009_battery","1"]
            3 -> ["3","3","act5d0_ex07","trap_009_battery","0"]
            4 -> ["4","3","act5d0_ex05","sktok_farm","0"]
            5 -> ["5","3","act11d0_08","6"]
            6 -> ["6","3","act11d0_06","trap_014_tower","0"]
            7 -> ["7","3","act11d0_04","trap_014_tower","0"]
            8 -> ["8","3","act21side_09","enemy_1284_sgprst","killed","1"]
            9 -> ["9","3","act21side_10","enemy_1535_wlfmster","wlfmster_cast_cage","2"]
            10 -> ["10","2","act2bossrush_tm03","victoria_kill_boss","1"]
            11 -> ["11","2","act12side_03","chock_withdraw","3"]
            12 -> ["12","3","act13side_06","char_496_wildmn^char_420_flamtl"]
            13 -> ["13","3","act21side_s04","char_427_vigil","1"]
            14 -> ["14","3","act17side_ex08","5","dsdevr_buff"]
            15 -> ["15","3","act17side_ex03","2","creep_damage"]
            16 -> ["16","2","act1bossrush_tm03","kazimierz","15"]
            17 -> ["17","2","act2bossrush_tm01","1","爆发"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for i in args[3].split("^"):
                    for n in self.battle_data["battleData"]["stats"]["skillTrigStats"]:
                        if i == n["Key"]:
                            count += n["Value"]
                if count >= args[4]:
                    self.UpdateMission(1)
        elif int(args[0]) == 2:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if args[3] in k:
                        count += v
                if count >= int(args[4]):
                    self.UpdateMission(1)
        elif int(args[0]) == 3:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if args[3] in k and v <= int(args[4]):
                        self.UpdateMission(1)
                        break
        elif int(args[0]) == 4:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if args[3] in k:
                        count += v
                if count <= int(args[4]):
                    self.UpdateMission(1)
        elif int(args[0]) == 5:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                if len(self.battle_data["battleData"]["stats"]["charList"]) <= args[3]:
                    self.UpdateMission(1)
        elif int(args[0]) == 6:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if args[3] in k:
                        count += v
                if v <= int(args[4]):
                    self.UpdateMission(1)
        elif int(args[0]) == 7:
            self.InitMission(1)
            count = 0
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if args[3] in k:
                        count += v
            if count <= int(args[4]):
                self.UpdateMission(1)
        elif int(args[0]) == 8:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if all(s in k for s in [args[3], args[4]]) and v >= int(args[5]):
                        self.UpdateMission(1)
                        break
        elif int(args[0]) == 9:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if all(s in k for s in [args[3], args[4]]):
                        count += v
                if count >= int(args[5]):
                    self.UpdateMission(1)
        elif int(args[0]) == 10:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if args[3] in k:
                        count += v
                if count >= int(args[4]):
                    self.UpdateMission(1)
        elif int(args[0]) == 11:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if args[3] in k:
                        count += v
                if count <= int(args[4]):
                    self.UpdateMission(1)
        elif int(args[0]) == 12:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for i in self.battle_data["battleData"]["stats"]["charStats"]:
                    if i["Key"]["counterType"] == "DEAD" and i["Key"]["charId"] in args[3].split("^"):
                        count += 1
                if count == 0:
                    self.UpdateMission(1)
        elif int(args[0]) == 13:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                if args[3] not in self.battle_data["battleData"]["stats"]["idList"]:
                    chars = [self.player_data["troop"]["chars"][i]["charId"] for i in [str(d["charInstId"]) for d in self.battle_info["ownSlots"]]]
                    if args[3] in chars:
                        self.UpdateMission(args[4])
        elif int(args[0]) == 14:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if args[4] in k:
                        count += 1
                if count >= int(args[3]):
                    self.UpdateMission(1)
        elif int(args[0]) == 15:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if args[4] in k:
                        count += v
                if count <= int(args[3]):
                    self.UpdateMission(1)
        elif int(args[0]) == 16:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
                count = 0
                for i in self.battle_data["battleData"]["stats"]["charStats"]:
                    if i["Key"]["counterType"] == "SPAWN" and CHARACTER_TABLE[i["Key"]["charId"]]["nationId"] == args[3]:
                        count += i["Value"]
                if count >= int(args[4]):
                    self.UpdateMission(1)
        elif int(args[0]) == 17:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
                chars = [self.player_data["troop"]["chars"][i]["charId"] for i in [str(d["charInstId"]) for d in self.battle_info["ownSlots"]]]
                count = 0
                for n in chars:
                    if args[4] in CHARACTER_TABLE[n]["tagList"]:
                        count += 1
                if count >= int(args[3]):
                    self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteStageOrCampaign(self, *args) -> None:
        '''
        Type:
            0：通关任意关卡<n>次

        Param example:
            0 -> ["0","40"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            if self.stage_id and self.battle_data["completeState"] >= 2:
                self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteStageSimpleAtLeastId(self, *args) -> None:
        '''
        Type:
            0：<n>星通关<stage>,且发射自走车的次数大于等于<m>次

        Param example:
            0 -> ["0","3","act20side_06","enemy_1265_durcar","born","10"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                    if all(s in k for s in [args[3], args[4]]):
                        count += v
                if count >= int(args[5]):
                    self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteStageSimpleAtMostId(self, *args) -> None:
        '''
        Type:
            0：通关<stage>，并阻止/避免<condition>

        Param example:
            0 -> [ "0","2","act20side_ex05","enemy_1263_durbus_2","take","8"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for i in self.battle_data["battleData"]["stats"]["extraBattleInfo"]:
                    if all(s in i for s in [args[3], args[4]]):
                        count += 1
                if count <= int(args[5]):
                    self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteStageWithCharm(self, *args) -> None:
        '''
        Type:
            0：携带至少<n>个稀有度为<m>的标志物通关<stage>

        Param example:
            0 -> ["0","3","act12side_s03", "0^1^2^3","5"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            writeLog(f"\033[1;31mUnsupported templateType: {args}\033[0;0m", "warning")  # TODO
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteStageWithRelic(self, *args) -> None:
        '''
        Type:
            0：启用<relic>通关<stages>，且累计部署干员<n>次
            1：启用<relic>通关<stages>，且使用<professions>干员击败<n>名敌人
            2：启用<relic>通关<stages>，且波次结束时未撤退的干员累计超过<n>人次
            3：启用<relic>通关<stages>，且小队中编入至少<n>种不同职业的干员
            4：启用<relic>通关<stages>，且小队中编入至少<n>位<professions>干员
            5：启用<relic>通关<stages>，且有至少<n>位干员在每个波次中都部署过

        Param example:
            0 -> ["0","act1bossrush_ex01^act1bossrush_ex02^act1bossrush_ex03^act1bossrush_ex04","act1bossrush_relic_01","50"]
            1 -> ["1","act1bossrush_ex01^act1bossrush_ex02^act1bossrush_ex03^act1bossrush_ex04","act1bossrush_relic_02","WARRIOR^SNIPER","20"]
            2 -> ["2","act2bossrush_ex01^act2bossrush_ex02^act2bossrush_ex03^act2bossrush_ex04","act2bossrush_relic_02","act2bossrush_relic2_buff","10"]
            3 -> ["3","act2bossrush_ex01^act2bossrush_ex02^act2bossrush_ex03^act2bossrush_ex04","act2bossrush_relic_03","6"]
            4 -> ["4","act2bossrush_ex01^act2bossrush_ex02^act2bossrush_ex03^act2bossrush_ex04","act2bossrush_relic_01","5","TANK^MEDIC"]
            5 -> ["5","act2bossrush_ex01^act2bossrush_ex02^act2bossrush_ex03^act2bossrush_ex04","act2bossrush_relic_04","1"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            for i in args[1].split("^"):
                count = 0
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    for n in self.battle_data["battleData"]["stats"]["charStats"]:
                        if n["Key"]["counterType"] == "SPAWN":
                            count += i["Value"]
                    if count >= int(args[3]) and any(args[2] in s for s in self.battle_data["battleData"]["stats"]["packedRuneDataList"]):
                        self.UpdateMission(1)
                        break
        elif int(args[0]) == 1:
            self.InitMission(1)
            for i in args[1].split("^"):
                count = 0
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
                    for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                        if "KILL_COUNT" in k:
                            char_id = k.split(',')[1]
                            if CHARACTER_TABLE[char_id]["profession"] in args[3].split("^"):
                                count += v
                    if count >= int(args[4]) and any(args[2] in s for s in self.battle_data["battleData"]["stats"]["packedRuneDataList"]):
                        self.UpdateMission(1)
                        break
        elif int(args[0]) == 2:
            self.InitMission(1)
            for i in args[1].split("^"):
                count = 0
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    for k, v in self.battle_data["battleData"]["stats"]["extraBattleInfo"].items():
                        if args[3] in k:
                            count += v
                    if count > int(args[4]) and any(args[2] in s for s in self.battle_data["battleData"]["stats"]["packedRuneDataList"]):
                        self.UpdateMission(1)
                        break
        elif int(args[0]) == 3:
            self.InitMission(1)
            for i in args[1].split("^"):
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
                    chars = [self.player_data["troop"]["chars"][i]["charId"] for i in [str(d["charInstId"]) for d in self.battle_info["ownSlots"]]]
                    profession = []
                    for n in chars:
                        if CHARACTER_TABLE[n]["profession"] not in profession:
                            profession.append(CHARACTER_TABLE[n]["profession"])
                    if len(profession) >= int(args[3]) and any(args[2] in s for s in self.battle_data["battleData"]["stats"]["packedRuneDataList"]):
                        self.UpdateMission(1)
                        break
        elif int(args[0]) == 4:
            self.InitMission(1)
            for i in args[1].split("^"):
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
                    chars = [self.player_data["troop"]["chars"][i]["charId"] for i in [str(d["charInstId"]) for d in self.battle_info["ownSlots"]]]

                    count = 0
                    for n in chars:
                        if CHARACTER_TABLE[n]["profession"] in args[4].split("^"):
                            count += 1
                    if count >= int(args[3]) and any(args[2] in s for s in self.battle_data["battleData"]["stats"]["packedRuneDataList"]):
                        self.UpdateMission(1)
                        break
        elif int(args[0]) == 5:
            self.InitMission(1)
            for i in args[1].split("^"):
                char_count = {}
                count = 0
                wave = 99
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    for n in self.battle_data["battleData"]["stats"]["extraBattleInfo"]:
                        if "MAX_BOSS_WAVE" in n:
                            wave = self.battle_data["battleData"]["stats"]["extraBattleInfo"][n]
                        if "DETAILED" in n:
                            char_id = n.split(',')[1]
                            char_count[char_id] = char_count.get(char_id, 0) + 1
                    for _, m in char_count.items():
                        if m == wave:
                            count += 1
                    if count > int(args[3]) and any(args[2] in s for s in self.battle_data["battleData"]["stats"]["packedRuneDataList"]):
                        self.UpdateMission(1)
                        break
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CompleteStageWithTechTree(self, *args) -> None:
        '''
        Type:
            0：<n>星通关<stage>，且最多只携带<m>个"小帮手"的组件

        Param example:
            0 -> ["0","3","act17side_ex07","tech_1;tech_2;tech_3;tech_4;tech_5","3"]
        '''
        if int(args[0]) == 0:
            self.InitMission(1)
            if args[2] == self.stage_id and self.battle_data["completeState"] >= int(args[1]):
                count = 0
                for i in self.battle_data["battleData"]["stats"]["packedRuneDataList"]:
                    if i in args[3]:
                        count += 1
                if count <= int(args[4]):
                    self.UpdateMission(1)
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CostAp(self, *args) -> None:
        '''
        Type:
            0：累计消耗<n>点理智

        Param example:
            0 -> ["0","2400"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            if self.stage_id and self.extra and self.battle_data["completeState"] >= 2 and "apCost" in self.extra:
                self.UpdateMission(self.extra["apCost"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CostGold(self, *args) -> None:
        '''
        Type:
            0：累计消耗<n>龙门币

        Param example:
            0 -> ["0","150000"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            if "goldCost" in self.extra:
                self.UpdateMission(self.extra["goldCost"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def CostGoldPlus(self, *args) -> None:
        '''
        Type:
            0：在干员升级和晋升中累计消耗<n>龙门币

        Param example:
            0 -> ["0","60000"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            if "goldCostPlus" in self.extra:
                self.UpdateMission(self.extra["goldCostPlus"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def DeliveryOrder(self, *args) -> None:
        '''
        Type:
            1：完成<n>笔订单

        Param example:
            1 -> ["0","150"]
        '''
        if int(args[0]) == 1:
            self.InitMission(int(args[1]))
            if "deliveryOrder" in self.extra:
                self.UpdateMission(self.extra["deliveryOrder"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def EnemyKill(self, *args) -> None:
        '''
        Type:
            0：在活动关卡中击败<n>个敌人

        Param example:
            0 -> ["0","act13d5_01^act13d5_tr01^act13d5_02","200"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[2]))
            for i in args[1].split("^"):
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    self.UpdateMission(self.battle_data["killCnt"])
                    break
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def GainIntimacy(self, *args) -> None:
        '''
        Type:
            0：在基建内与干员进行<n>次增加信赖的互动

        Param example:
            0 -> ["0","200"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            if "gainIntimacyCount" in self.extra:
                self.UpdateMission(self.extra["gainIntimacyCount"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def ManufactureItem(self, *args) -> None:
        '''
        Type:
            0：在制造站生产<n>件赤金

        Param example:
            0 -> ["0","300","3003"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            if "manufactureItem" in self.extra:
                self.UpdateMission(self.extra["manufactureItem"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def NormalGacha(self, *args) -> None:
        '''
        Type:
            0：累计公开招募<n>次

        Param example:
            0 -> ["0","-1","25"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[2]))
            if "normalGachaCount" in self.extra:
                self.UpdateMission(self.extra["normalGachaCount"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def RecoverCharBaseAp(self, *args) -> None:
        '''
        Type:
            0：让<n>名干员在宿舍中恢复心情

        Param example:
            0 -> ["0","300"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            if "recoverCharBaseAp" in self.extra:
                self.UpdateMission(self.extra["recoverCharBaseAp"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def SendClue(self, *args) -> None:
        '''
        Type:
            0：向好友赠送<n>份线索

        Param example:
            0 -> ["0","18"]
        '''
        if int(args[0]) == 0:
            self.InitMission(int(args[1]))
            if "sendClue" in self.extra:
                self.UpdateMission(self.extra["sendClue"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def StageWithCondition(self, *args) -> None:
        '''
        Type:
            0：在<stages>中，累计击败<n>个<enemy>
            1：<stages>中累计使用技能<n>次
            2：<stages>中累计部署干员<n>次

        Param example:
            0 -> ["0","act17side_01^act17side_02^act17side_03","enemy_1160_hvyslr","6"]
            1 -> ["1","act17side_01^act17side_02^act17side_03","50"]
            2 -> ["2","act17side_01^act17side_02^act17side_03","40"]
        '''
        for i in args[1].split("^"):
            if int(args[0]) == 0:
                self.InitMission(int(args[3]))
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    for n in self.battle_data["battleData"]["stats"]["enemyStats"]:
                        if n["Key"]["enemyId"] == args[2] and n["Key"]["counterType"] == "HP_ZERO":
                            self.UpdateMission(n["Value"])
                            break
            elif int(args[0]) == 1:
                self.InitMission(int(args[2]))
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    count = 0
                    for n in self.battle_data["battleData"]["stats"]["skillTrigStats"]:
                        count += n["Value"]
                    self.UpdateMission(count)
                    break
            elif int(args[0]) == 2:
                self.InitMission(int(args[2]))
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    count = 0
                    for n in self.battle_data["battleData"]["stats"]["charStats"]:
                        if n["Key"]["counterType"] == "SPAWN":
                            count += n["Value"]
                    self.UpdateMission(count)
                    break
            else:
                writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def StageWithEnemyKill(self, *args) -> None:
        '''
        Type:
            1: 累计击败任意<n>名敌兵
            2：通关多维合作<stage>，累积歼灭<n>个<enemies>
            5：<stages>中累计击败<n>名敌人
            6：尝试挑战关卡<stage>并至少造成<n>歼灭数

        Param example:
            1 -> ["1","600"]
            2 -> ["2","25","enemy_4001_toxcar^enemy_4001_toxcar_2"]
            5 -> ["5","act17side_01^act17side_02^act17side_03","100"]
            6 -> ["6","act20side_mo01","50", "1"]
        '''
        if int(args[0]) == 1:
            self.InitMission(int(args[1]))
            if self.stage_id and self.battle_data["completeState"] >= 2:
                self.UpdateMission(self.battle_data["killCnt"])
        elif int(args[0]) == 2:
            self.InitMission(int(args[1]))
            if self.stage_id and self.battle_data["completeState"] >= 2:
                count = 0
                for i in args[2].split("^"):
                    for n in self.battle_data["battleData"]["stats"]["enemyStats"]:
                        if n["Key"]["enemyId"] == i and n["Key"]["counterType"] == "HP_ZERO":
                            count += n["Value"]
            self.UpdateMission(count)
        elif int(args[0]) == 5:
            self.InitMission(int(args[2]))
            for i in args[1].split("^"):
                if i == self.stage_id and self.battle_data["completeState"] >= 2:
                    self.UpdateMission(self.battle_data["killCnt"])
                    break
        elif int(args[0]) == 6:
            self.InitMission(int(args[3]))
            for i in args[1].split("^"):
                if i == self.stage_id and self.battle_data["completeState"] >= int(args[3]):
                    if self.battle_data["killCnt"] >= int(args[2]):
                        self.UpdateMission(int(args[3]))
                        break
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def StartInfoShare(self, *args) -> None:
        '''
        Type:
            1：任务期间累积举行<n>次线索交流

        Param example:
            1 -> ["1","3"]
        '''
        if int(args[0]) == 1:
            self.InitMission(int(args[1]))
            if "infoShareCount" in self.extra:
                self.UpdateMission(self.extra["infoShareCount"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")

    def UpgradeChar(self, *args) -> None:
        '''
        Type:
            2：累计提升<n>点干员经验值

        Param example:
            2 -> ["0","60000"]
        '''
        if int(args[0]) == 2:
            self.InitMission(int(args[1]))
            if "upgradeCharExp" in self.extra:
                self.UpdateMission(self.extra["upgradeCharExp"])
        else:
            writeLog(f"\033[1;31mUnknown templateType: {args}\033[0;0m", "error")


# === Act13sideCompleteDailyMission Check ===

# === Act20sideApprovalCar Check ===

# === Act20sideConfirmExhiCar Check ===

# === Act20sideGainAccessories Check ===

# === Act20sidePassStageWithCar Check ===

# === Act20sideSeekAccessories Chek ===

# === BuyShopItem Check ===

# === CompleteAnyMulStage Check ===

# === CompleteAnyStage Check ===

# === CompleteCampaign Check ===

# === CompleteDailyStage Check ===

# === CompleteInterlockStage Check ===

# === CompleteMainStage Check ===

# === CompleteStage Check ===

# === CompleteStageAct Check ===

# === CompleteStageAct Check ===

# === CompleteStageCondition Check ===

# === CompleteStageOrCampaign Check ===

# === CompleteStageSimpleAtLeastId Check ===

# === CompleteStageSimpleAtMostId Check ===

# === CompleteStageWithCharm Check ===

# === CompleteStageWithRelic Check ===
# 0 - Pass
# 1 - Pass
# 2 - Pass
# 3 - Pass
# 4 - Pass
# 5 - Pass
# === CompleteStageWithTechTree Check ==

# === CostAp Check ===

# === CostGold Check ===

# === CostGold Plus Check ===

# === DeliveryOrder Check ===

# === EnemyKill Check ===

# === GainIntimacy Check ===

# === ManufactureItem Check ===

# === NormalGacha Check ===

# === RecoverCharBaseAp Check ===

# === SendClue Check ===

# === StageWithCondition Check ===

# === StageWithEnemyKill Check ===

# === StartInfoShare Check ===

# === UpgradeChar Check ===
