import traceback
import webbrowser
from wsgiref.simple_server import make_server

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from constants import CONFIG_PATH
from utils import read_json

import account, activity, background, building, campaignV2, char, charBuild, charm, crisis, \
    deepsea, gacha, logger, mail, quest, pay, rlv2, shop, social, story, storyreview, tower, user, \
    asset.assetbundle, auth.online, auth.user, auth.u8, config.prod, core.database.initDatabase

server_config = read_json(CONFIG_PATH)
core.database.initDatabase.initDB()

app = Flask(__name__)
# app.config["SECRET_KEY"] = "HRMCwPonJLIB3WCl"
# CSRFProtect(app)

host = server_config["server"]["host"]
port = server_config["server"]["port"]
WSGIServer = False


@app.errorhandler(Exception)
def handle_exceptions(error):
    if not hasattr(error, "code"):
        logger.writeLog(f"{error} - {traceback.format_exc()}", "error")
        return "", 502
    return error

# TODO: Add Web-UI
# app.add_url_rule('/', methods=['GET', 'POST'], view_func=admin.index.index)
# app.add_url_rule('/login', methods=['GET', 'POST'], view_func=admin.login.login)


app.add_url_rule('/account/login', methods=['POST'], view_func=account.accountLogin)
app.add_url_rule('/account/syncData', methods=['POST'], view_func=account.accountSyncData)
app.add_url_rule('/account/syncStatus', methods=['POST'], view_func=account.accountSyncStatus)

app.add_url_rule('/activity/bossRush/battleStart', methods=['POST'], view_func=activity.activityBossRushBattleStart)
app.add_url_rule('/activity/bossRush/battleFinish', methods=['POST'], view_func=activity.activityBossRushBattleFinish)
app.add_url_rule('/activity/bossRush/relicSelect', methods=['POST'], view_func=activity.activityBossRushRelicSelect)
app.add_url_rule('/activity/bossRush/relicUpgrade', methods=['POST'], view_func=activity.activityBossRushRelicUpgrade)
app.add_url_rule('/activity/confirmActivityMission', methods=['POST'], view_func=activity.activityConfirmActivityMission)
app.add_url_rule('/activity/confirmActivityMissionList', methods=['POST'], view_func=activity.activityConfirmActivityMissionList)
app.add_url_rule('/activity/rewardMilestone', methods=['POST'], view_func=activity.activityRewardMilestone)
app.add_url_rule('/activity/rewardAllMilestone', methods=['POST'], view_func=activity.activityRewardAllMilestone)

app.add_url_rule('/assetbundle/official/Android/assets/<string:assetsHash>/<string:fileName>', methods=['GET', 'POST'], view_func=asset.assetbundle.getFile)

app.add_url_rule('/background/setBackground', methods=['POST'], view_func=background.backgroundSetBackground)

app.add_url_rule('/building/sync', methods=['POST'], view_func=building.buildingSync)

app.add_url_rule('/campaignV2/battleStart', methods=['POST'], view_func=campaignV2.campaignV2BattleStart)
app.add_url_rule('/campaignV2/battleFinish', methods=['POST'], view_func=campaignV2.campaignV2BattleFinish)
app.add_url_rule('/campaignV2/battleSweep', methods=['POST'], view_func=campaignV2.campaignV2BattleSweep)

app.add_url_rule('/char/changeMarkStar', methods=['POST'], view_func=char.charChangeMarkStar)

app.add_url_rule('/charBuild/addonStage/battleStart', methods=['POST'], view_func=quest.questBattleStart)
app.add_url_rule('/charBuild/addonStage/battleFinish', methods=['POST'], view_func=quest.questBattleFinish)
app.add_url_rule('/charBuild/addonStory/unlock', methods=['POST'], view_func=charBuild.charBuildaddonStoryUnlock)
app.add_url_rule('/charBuild/batchSetCharVoiceLan', methods=['POST'], view_func=charBuild.charBuildBatchSetCharVoiceLan)
app.add_url_rule('/charBuild/setCharVoiceLan', methods=['POST'], view_func=charBuild.charBuildSetCharVoiceLan)
app.add_url_rule('/charBuild/setDefaultSkill', methods=['POST'], view_func=charBuild.charBuildSetDefaultSkill)
app.add_url_rule('/charBuild/changeCharSkin', methods=['POST'], view_func=charBuild.charBuildChangeCharSkin)
app.add_url_rule('/charBuild/setEquipment', methods=['POST'], view_func=charBuild.charBuildSetEquipment)
app.add_url_rule('/charBuild/changeCharTemplate', methods=['POST'], view_func=charBuild.charBuildChangeCharTemplate)

app.add_url_rule('/charm/setSquad', methods=['POST'], view_func=charm.charmSetSquad)

app.add_url_rule('/config/prod/announce_meta/Android/preannouncement.meta.json', methods=['GET'], view_func=config.prod.prodPreAnnouncement)
app.add_url_rule('/config/prod/announce_meta/Android/announcement.meta.json', methods=['GET'], view_func=config.prod.prodAnnouncement)
app.add_url_rule('/config/prod/official/Android/version', methods=['GET'], view_func=config.prod.prodAndroidVersion)
app.add_url_rule('/config/prod/official/network_config', methods=['GET'], view_func=config.prod.prodNetworkConfig)
app.add_url_rule('/config/prod/official/refresh_config', methods=['GET'], view_func=config.prod.prodRefreshConfig)
app.add_url_rule('/config/prod/official/remote_config', methods=['GET'], view_func=config.prod.prodRemoteConfig)

app.add_url_rule('/crisis/getInfo', methods=['POST'], view_func=crisis.crisisGetCrisisInfo)
app.add_url_rule('/crisis/battleStart', methods=['POST'], view_func=crisis.crisisBattleStart)
app.add_url_rule('/crisis/battleFinish', methods=['POST'], view_func=crisis.crisisBattleFinish)

app.add_url_rule('/deepSea/branch', methods=['POST'], view_func=deepsea.deepSeaBranch)
app.add_url_rule('/deepSea/event', methods=['POST'], view_func=deepsea.deepSeaEvent)

app.add_url_rule('/gacha/advancedGacha', methods=['POST'], view_func=gacha.gachaAdvancedGacha)
app.add_url_rule('/gacha/boostNormalGacha', methods=['POST'], view_func=gacha.gachaBoostNormalGacha)
app.add_url_rule('/gacha/cancelNormalGacha', methods=['POST'], view_func=gacha.gachaCancelNormalGacha)
app.add_url_rule('/gacha/finishNormalGacha', methods=['POST'], view_func=gacha.gachaFinishNormalGacha)
app.add_url_rule('/gacha/getPoolDetail', methods=['POST'], view_func=gacha.gachaGetPoolDetail)
app.add_url_rule('/gacha/syncNormalGacha', methods=['POST'], view_func=gacha.gachaSyncNormalGacha)
app.add_url_rule('/gacha/tenAdvancedGacha', methods=['POST'], view_func=gacha.gachaTenAdvancedGacha)
app.add_url_rule('/gacha/normalGacha', methods=['POST'], view_func=gacha.gachaNormalGacha)

app.add_url_rule('/mail/getMetaInfoList', methods=['POST'], view_func=mail.mailGetMetaInfoList)
app.add_url_rule('/mail/listMailBox', methods=['POST'], view_func=mail.mailListMailBox)
app.add_url_rule('/mail/receiveMail', methods=['POST'], view_func=mail.mailReceiveMail)
app.add_url_rule('/mail/receiveAllMail', methods=['POST'], view_func=mail.mailReceiveAllMail)
app.add_url_rule('/mail/removeAllReceivedMail', methods=['POST'], view_func=mail.mailRemoveAllReceivedMail)

app.add_url_rule('/online/v1/ping', methods=['POST'], view_func=auth.online.onlineV1Ping)
app.add_url_rule('/online/v1/loginout', methods=['POST'], view_func=auth.online.onlineV1LoginOut)

app.add_url_rule('/pay/confirmOrder', methods=['POST'], view_func=pay.payConfirmOrder)
app.add_url_rule('/pay/confirmOrderAlipay', methods=['POST'], view_func=pay.payConfirmOrderAlipay)
app.add_url_rule('/pay/confirmOrderWechat', methods=['POST'], view_func=pay.payConfirmOrderWechat)
app.add_url_rule('/pay/createOrder', methods=['POST'], view_func=pay.payCreateOrder)
app.add_url_rule('/pay/createOrderAlipay', methods=['POST'], view_func=pay.payCreateOrderAlipay)
app.add_url_rule('/pay/createOrderWechat', methods=['POST'], view_func=pay.payCreateOrderWechat)
app.add_url_rule('/pay/success', methods=['POST'], view_func=pay.paySuccess)
app.add_url_rule('/pay/getUnconfirmedOrderIdList', methods=['POST'], view_func=pay.payGetUnconfirmedOrderIdList)
app.add_url_rule('/u8/pay/confirmOrderState', methods=['POST'], view_func=auth.u8.payConfirmOrderState)
app.add_url_rule('/u8/pay/getAllProductList', methods=['POST'], view_func=auth.u8.payGetAllProductList)

app.add_url_rule('/quest/battleStart', methods=['POST'], view_func=quest.questBattleStart)
app.add_url_rule('/quest/battleFinish', methods=['POST'], view_func=quest.questBattleFinish)
app.add_url_rule('/quest/finishStoryStage', methods=['POST'], view_func=quest.questFinishStoryStage)
app.add_url_rule('/quest/saveBattleReplay', methods=['POST'], view_func=quest.questSaveBattleReplay)
app.add_url_rule('/quest/getBattleReplay', methods=['POST'], view_func=quest.questGetBattleReplay)
app.add_url_rule('/quest/changeSquadName2', methods=['POST'], view_func=quest.questChangeSquadName)
app.add_url_rule('/quest/squadFormation', methods=['POST'], view_func=quest.questSquadFormation)
app.add_url_rule('/quest/getAssistList', methods=['POST'], view_func=quest.questGetAssistList)

app.add_url_rule('/rlv2/createGame', methods=['POST'], view_func=rlv2.rlv2CreateGame)
app.add_url_rule('/rlv2/chooseInitialRelic', methods=['POST'], view_func=rlv2.rlv2ChooseInitialRelic)
app.add_url_rule('/rlv2/selectChoice', methods=['POST'], view_func=rlv2.rlv2SelectChoice)
app.add_url_rule('/rlv2/chooseInitialRecruitSet', methods=['POST'], view_func=rlv2.rlv2ChooseInitialRecruitSet)
app.add_url_rule('/rlv2/activeRecruitTicket', methods=['POST'], view_func=rlv2.rlv2ActiveRecruitTicket)
app.add_url_rule('/rlv2/recruitChar', methods=['POST'], view_func=rlv2.rlv2RecruitChar)
app.add_url_rule('/rlv2/closeRecruitTicket', methods=['POST'], view_func=rlv2.rlv2CloseRecruitTicket)
app.add_url_rule('/rlv2/finishEvent', methods=['POST'], view_func=rlv2.rlv2FinishEvent)
app.add_url_rule('/rlv2/moveAndBattleStart', methods=['POST'], view_func=rlv2.rlv2MoveAndBattleStart)

app.add_url_rule('/shop/buyEPGSGood', methods=['POST'], view_func=shop.shopBuyEPGSGood)
app.add_url_rule('/shop/buyExtraGood', methods=['POST'], view_func=shop.shopBuyExtraGood)
app.add_url_rule('/shop/buyFurniGood', methods=['POST'], view_func=shop.shopBuyFurniGood)
app.add_url_rule('/shop/buyFurniGroup', methods=['POST'], view_func=shop.shopBuyFurniGroup)
app.add_url_rule('/shop/buyHighGood', methods=['POST'], view_func=shop.shopBuyHighGood)
app.add_url_rule('/shop/buyLowGood', methods=['POST'], view_func=shop.shopBuyLowGood)
app.add_url_rule('/shop/buyRepGood', methods=['POST'], view_func=shop.shopBuyRepGood)
app.add_url_rule('/shop/buySkinGood', methods=['POST'], view_func=shop.shopBuySkinGood)
app.add_url_rule('/shop/getCashGoodList', methods=['POST'], view_func=shop.shopGetCashGoodList)
app.add_url_rule('/shop/getGoodPurchaseState', methods=['POST'], view_func=shop.shopGetGoodPurchaseState)
app.add_url_rule('/shop/getGPGoodList', methods=['POST'], view_func=shop.shopGetGPGoodList)
app.add_url_rule('/shop/getEPGSGoodList', methods=['POST'], view_func=shop.shopGetEPGSGoodList)
app.add_url_rule('/shop/getExtraGoodList', methods=['POST'], view_func=shop.shopGetExtraGoodList)
app.add_url_rule('/shop/getFurniGoodList', methods=['POST'], view_func=shop.shopGetFurniGoodList)
app.add_url_rule('/shop/getHighGoodList', methods=['POST'], view_func=shop.shopGetHighGoodList)
app.add_url_rule('/shop/getLowGoodList', methods=['POST'], view_func=shop.shopGetLowGoodList)
app.add_url_rule('/shop/getRepGoodList', methods=['POST'], view_func=shop.shopGetRepGoodList)
app.add_url_rule('/shop/getSkinGoodList', methods=['POST'], view_func=shop.shopGetSkinGoodList)

app.add_url_rule('/social/deleteFriend', methods=['POST'], view_func=social.socialDeleteFriend)
app.add_url_rule('/social/getSortListInfo', methods=['POST'], view_func=social.socialGetSortListInfo)
app.add_url_rule('/social/getFriendList', methods=['POST'], view_func=social.socialGetFriendList)
app.add_url_rule('/social/getFriendRequestList', methods=['POST'], view_func=social.socialGetFriendRequestList)
app.add_url_rule('/social/processFriendRequest', methods=['POST'], view_func=social.socialProcessFriendRequest)
app.add_url_rule('/social/searchPlayer', methods=['POST'], view_func=social.socialSearchPlayer)
app.add_url_rule('/social/sendFriendRequest', methods=['POST'], view_func=social.socialSendFriendRequest)
app.add_url_rule('/social/setAssistCharList', methods=['POST'], view_func=social.socialSetAssistCharList)
app.add_url_rule('/social/setCardShowMedal', methods=['POST'], view_func=social.socialSetCardShowMedal)
app.add_url_rule('/social/setFriendAlias', methods=['POST'], view_func=social.socialSetFriendAlias)

app.add_url_rule('/story/finishStory', methods=['POST'], view_func=story.storyFinishStory)

app.add_url_rule('/storyreview/markStoryAcceKnown', methods=['POST'], view_func=storyreview.storyreviewMarkStoryAcceKnown)
app.add_url_rule('/storyreview/readStory', methods=['POST'], view_func=storyreview.storyreviewReadStory)

app.add_url_rule('/tower/createGame', methods=['POST'], view_func=tower.towerCreateGame)
app.add_url_rule('/tower/battleStart', methods=['POST'], view_func=tower.towerBattleStart)
app.add_url_rule('/tower/battleFinish', methods=['POST'], view_func=tower.towerBattleFinish)
app.add_url_rule('/tower/settleGame', methods=['POST'], view_func=tower.towerSettleGame)
app.add_url_rule('/tower/initGodCard', methods=['POST'], view_func=tower.towerInitGodCard)
app.add_url_rule('/tower/initGame', methods=['POST'], view_func=tower.towerInitGame)
app.add_url_rule('/tower/initCard', methods=['POST'], view_func=tower.towerInitCard)
app.add_url_rule('/tower/chooseSubGodCard', methods=['POST'], view_func=tower.towerChooseSubGodCard)
app.add_url_rule('/tower/recruit', methods=['POST'], view_func=tower.towerRecruit)
app.add_url_rule('/tower/layerReward', methods=['POST'], view_func=tower.towerLayerReward)

app.add_url_rule('/user/auth', methods=['POST'], view_func=auth.user.userAuth)
app.add_url_rule('/user/authenticateUserIdentity', methods=['POST'], view_func=auth.user.userAuthenticateUserIdentity)
app.add_url_rule('/user/bindNickName', methods=['POST'], view_func=user.userBindNickName)
app.add_url_rule('/user/buyAp', methods=['POST'], view_func=user.userBuyAp)
app.add_url_rule('/user/changeAvatar', methods=['POST'], view_func=user.userChangeAvatar)
app.add_url_rule('/user/changeResume', methods=['POST'], view_func=user.userChangeResume)
app.add_url_rule('/user/changePassword', methods=['POST'], view_func=auth.user.userChangePassword)
app.add_url_rule('/user/changePhone', methods=['POST'], view_func=auth.user.userChangePhone)
app.add_url_rule('/user/changePhoneCheck', methods=['POST'], view_func=auth.user.userChangePhoneCheck)
app.add_url_rule('/user/changeSecretary', methods=['POST'], view_func=user.userChangeSecretary)
app.add_url_rule('/user/checkIdCard', methods=['POST'], view_func=auth.user.userCheckIdCard)
app.add_url_rule('/user/checkIn', methods=['POST'], view_func=user.userCheckIn)
app.add_url_rule('/user/exchangeDiamondShard', methods=['POST'], view_func=user.userExchangeDiamondShard)
app.add_url_rule('/user/info/v1/need_cloud_auth', methods=['POST'], view_func=auth.user.userV1NeedCloudAuth)
app.add_url_rule('/user/login', methods=['POST'], view_func=auth.user.userLogin)
app.add_url_rule('/user/loginBySmsCode', methods=['POST'], view_func=auth.user.userLoginBySmsCode)
app.add_url_rule('/user/oauth2/v1/grant', methods=['POST'], view_func=auth.user.userOAuth2V1Grant)
app.add_url_rule('/user/oauth2/v1/unbind_grant', methods=['POST'], view_func=auth.user.userOauth2V1UnbindGrant)
app.add_url_rule('/user/register', methods=['POST'], view_func=auth.user.userRegister)
app.add_url_rule('/user/sendSmsCode', methods=['POST'], view_func=auth.user.userSendSmsCode)
app.add_url_rule('/user/updateAgreement', methods=['POST'], view_func=auth.user.userUpdateAgreement)
app.add_url_rule('/user/useRenameCard', methods=['POST'], view_func=user.userUseRenameCard)
app.add_url_rule('/user/v1/guestLogin', methods=['POST'], view_func=auth.user.userV1GuestLogin)
app.add_url_rule('/user/info/v1/send_phone_code', methods=['POST'], view_func=auth.user.userInfoV1SendPhoneCode)
app.add_url_rule('/u8/user/v1/getToken', methods=['POST'], view_func=auth.u8.userV1getToken)
app.add_url_rule('/u8/user/verifyAccount', methods=['POST'], view_func=auth.u8.userV1getToken)

if __name__ == "__main__":
    logger.writeLog(f"\033[1;35m[SERVER]\033[0;0m Server started at \033[1;32mhttp://{host}:{str(port)}\033[0;0m", "info")
    # webbrowser.open(f'http://{host}:{str(port)}/login') # TODO: Add Web-UI
    if WSGIServer:
        server = make_server(host, port, app)
        server.serve_forever()
    else:
        app.run(host=host, port=port, debug=True)
