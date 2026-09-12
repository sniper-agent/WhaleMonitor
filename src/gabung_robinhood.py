import csv
import os
from collections import Counter

MASTER = r"E:\WhaleMonitor\data\whale_wallet_master.csv"
BACKUP = r"E:\WhaleMonitor\data\whale_wallet_master.bak.csv"

RH = {
    "0x000461a73d3985eef4923655782aa5d0de75c111": "$BONER",
    "0x0029fddf90bdc332edfd07297142dd07a6087f10": "$HOODRAT",
    "0x00d78daf782921b27a6b407d34f19842c10a4a6b": "$MEME",
    "0x02f130f25169a36a2b3939f2ce56fa449ce1e22c": "$STONKBROKER",
    "0x037f67151f03016a0dc0138c239ee59619cfe8d5": "$YOLO",
    "0x0cc7cedb0935ceab0b4a6b38ee7dcfd403b19a7b": "$PONS",
    "0x0d8d6c105629e472691f9a970a6f70899195b5e0": "$YOLO",
    "0x0f982b092a46dda8d63bbe1e2947e16517dd1a14": "$PIPEDOG",
    "0x10cc6bd38112cac182db90b6a71d8bb5939526ba": "$PONS",
    "0x1125b539f93cd6875c85622e0cc80404a6f61222": "$HOODRAT",
    "0x11d4f04369e8d75b341473fc82d4069292776354": "$PIPEDOG",
    "0x1338c1a92368e36e072d7d2e146b093e03e20d77": "$VLAD",
    "0x1540fbdb4f2a5d5addffcc64a3abed5bdeeac3e9": "$VLAD",
    "0x1584561d1521ff475367185bcde3a04fde42823a": "$HOODRAT",
    "0x16f5ef133d0d15b196a778d22bf1ec56f8f37c05": "$MEME",
    "0x17f5a93909becee47618a368f88876d710005897": "$HOODRAT",
    "0x182c735e6c7fdc9e8c6f3f3823e8c0556d6142df": "$HOODRAT",
    "0x1d4f6f17baa6e2938ec4f5e8a68c68348a058560": "$SLINK",
    "0x1feea8c261fa410c51647ba52f749900fe1b7751": "$HOODRAT",
    "0x22055b5799d9b98e002b28f15fb2acb08ed5eee7": "$AI",
    "0x22b58176fd87a0d98bac34b5cc75ffecb64add71": "$PONS",
    "0x25c93dac3a72e48e67314709f058ccf56c0cf43a": "$PONS",
    "0x2874dc337f5821b5fa832bbc305107dc4a57608e": "$YOLO",
    "0x2a129a2cd8250136ed60ce99ace6153096ea8939": "$VLAD",
    "0x2a8d459151647fd6b50d415ce512b6f46f76b775": "$AI",
    "0x2aa9da61eff59037eb661e2784eb405673c19263": "$YOLO",
    "0x2b0d0183d017c58b924401ca8ac362f6e01f0e9e": "$HMM",
    "0x2b1e0bcefada121c5bc484a546e3ca0e2a8bee5b": "$AI",
    "0x2bdf1a698d39a4358e2c162deacc038fadb8a9d5": "$TENDIES",
    "0x323a535ec0cdaeacac8904dc93544664a58ef1b6": "$BONER",
    "0x342744fcdfa9742bb17773f7caf60f75f83b8125": "$BONER",
    "0x35d42cacaa7f8958ab2427bfbfb29d73cf24dad6": "$HOODRAT",
    "0x3bc4d5c3c85ec442160849ac70e16a2e24579668": "$PIPEDOG",
    "0x3d8aa3b4c58fe7f9f13e1d87ac144b276cb07eea": "$HOODRAT",
    "0x40fdcd9d2e5862da56f4655778d0180df75b2f53": "$CASHCAT",
    "0x41c87cb6584be617809023aa22e63df2c9650bed": "$YOLO",
    "0x43f2c32fb92d88de4bac3258a3a92c1cb0d75c0b": "$AI",
    "0x4c8ff71b1cf08ea9652229cd09427dc1b3ec12f0": "$PIPEDOG",
    "0x4e2bce37385cfdc923599b69080b217603cc4eac": "$PIPEDOG",
    "0x4e3468951d49f2eea976ed0d6e75ffcb44a9a544": "$AI, $BONER, $MEME",
    "0x4e8649be40ae67ebbcff99c291b92ee03015917b": "$CASHCAT",
    "0x4f55879a6683c2cb46f9710678dbc8c49ea54f5b": "$SLINK",
    "0x50e43b43a8ee1e07e0ac978e92adff7dfbfb88e7": "$PONS",
    "0x50f27cdb650879a41fb07038bf2b818845c20e17": "$AI, $BONER",
    "0x54d209d9d224a615e0e5f0476644886897b75e45": "$CASHCAT",
    "0x55e1d60c15174e9e06d7e125169933feace1de46": "$TENDIES",
    "0x5638484ba2d2f1d1d35020572b0aa439a9869192": "$BONER, $CASHCAT, $TENDIES",
    "0x5678c23be6989cde5d0fe68d921584b4404a3180": "$STONKBROKER",
    "0x56d317b87344538de94371a1593613a4bd6fa7a4": "$HMM",
    "0x589d84a20cac79a35dd5aaf9ca8edd683330ca4d": "$STONKBROKER",
    "0x5b43c6264ce8ec9ba4ae62de9a43a158e4c9b460": "$SLINK",
    "0x5d81d3051ddd4e929c76bc572d4f1586c7b752ad": "$STONKBROKER",
    "0x5f60a59f2d243d533f82fd9844149d56ff363659": "$AI",
    "0x6687b0b32845e3e1ff8adb0d8ba2fc2d39adc840": "$SLINK",
    "0x678da315c3852a9a810fc630a3e7c891fda4c3bd": "$VLAD",
    "0x6b51c88b57f73cb671ff858b8024837e58980100": "$SLINK",
    "0x6f7c505458ddf8ed574db46786bb82c48e1e6add": "$SLINK",
    "0x6fc4a0b5c5ef56f53328dbbc03454592b5b720a8": "$YOLO",
    "0x7130d0ab931e62751deae5d2e38b640d329980da": "$MEME",
    "0x72774e2fe1992d5da8c6e9cef73fd2ab980c0b98": "$PONS",
    "0x77acc36fcc41dc3bfb51441e003831c74d4ecaf0": "$CASHCAT",
    "0x7ccdb7b7c98a366e5c529ce30ad70bcf31e54706": "$VLAD",
    "0x7e3ba68c49561aae7c23c1d20fef0f1d7615a3ad": "$HMM",
    "0x7f9b4c760ef21958a8ea19a70a98a5bfc3dac8de": "$TENDIES",
    "0x7fac2160bab6d465107a10a1b13f6e7ebe8b4a2c": "$HMM",
    "0x81a997def5fc553f5854c964600d95132161d317": "$YOLO",
    "0x81f9cd9a1123f36c8f301e940ee40fc7c2fa4b3e": "$HOODRAT",
    "0x8366a39cc670b4001a1121b8f6a443a643e40951": "$CASHCAT, $PIPEDOG, $PONS",
    "0x8a494ed488c5bc157e0fb2983fdfb90e2d63b691": "$MEME",
    "0x8b61615ac4c5e69382527bf0496794f6415dd8fa": "$STONKBROKER",
    "0x8fabe392df90b06ad610c33f41bb1abd78a5fc20": "$STONKBROKER",
    "0x942aac2a6603501473a4685471284798df6c3679": "$YOLO",
    "0x951f44a0f7941155ddf6fd937353aa55b3b0227c": "$HOODRAT",
    "0x96962a9fa7ed1c3a306c5948cb8997208d11c354": "$TENDIES",
    "0x97047b79efc5c9ece21b6230e67eb500037ce850": "$BONER",
    "0x9cf5dec27768855d478152128851ebde74f6a3ed": "$HMM",
    "0x9e06d046be4e304c8ff22d2526a3370d973c390f": "$PIPEDOG",
    "0xa01ed60b443967bbdff6bf7511c7e2ae5d3c6268": "$VLAD",
    "0xa3e3376b2395d6e598dba44e3609310b0b6f90bc": "$TENDIES",
    "0xa563903a5156b3504e58d3e8d037bedee5bd7b5a": "$BONER",
    "0xa70fc67c9f69da90b63a0e4c05d229954574e313": "$CASHCAT",
    "0xa7bd8231281ce6a2ef840a9fce2c2557e5219473": "$STONKBROKER",
    "0xac6da909f2132e680aa4998263da00f519c1946b": "$CASHCAT",
    "0xae15d608f33293cbd881f4b647a76d7eaa477b3c": "$SLINK",
    "0xaee728455cd103e735a368cb3d388561bb156a16": "$YOLO",
    "0xb1c426d94db2a16aa0a3310966c29eb1db4ad774": "$VLAD",
    "0xb1fd2862967598e2f207900a9c2cf20609d51954": "$SLINK",
    "0xb5b731f340554b672f686ca8459d55ced5e5bda4": "$BONER",
    "0xb8f305f27ccc406373de0082cc06cb1d065504ea": "$AI",
    "0xb990465dc0293082fabc4afb03c35539503b4eab": "$HMM",
    "0xbbfdb63384412a55bc822e6702ecd4cf85daa09f": "$YOLO",
    "0xbd2895dc008c31ba7b2e9177ebec4e7b048acb86": "$STONKBROKER",
    "0xbf732ea04197942783e34730ed6e0f6099575d58": "$TENDIES",
    "0xc4a21f9d6485fc5893dd4a491b320a83daf4da1d": "$AI",
    "0xc52fbb9c4a7373b85de6415f888e5e2e3f195176": "$TENDIES",
    "0xc62d0d47ffd7494ed86325f20d4adb7a0faee263": "$PIPEDOG",
    "0xca1182abf370b85a4e5d61903ea561bb38579e09": "$SLINK",
    "0xcbcefc4f269b19b7c492be26443b4cd71357d58c": "$SLINK",
    "0xcc708a199b8565c09ba2c0bd5fefa53aaf2036dc": "$HMM",
    "0xd1bf5f917ea367b37cb4eec6d41d8433a12fc8fd": "$TENDIES",
    "0xd42a491087a15e5afd51feb3606066cc152d2b09": "$CASHCAT",
    "0xd4a6f030f9c555c0f74be298f83837f356e2ace3": "$STONKBROKER",
    "0xd4de9eba1a5521af7c76052b2f216ac6618ea9e0": "$PIPEDOG",
    "0xd70627fd9ee5b70906620a6f2001ba74457b438d": "$VLAD",
    "0xda15b2fd4eb7967039c7e46e69de77fee2e235df": "$HMM",
    "0xda6fad6284d5920fad1418d29ac28ec146f4e61d": "$MEME",
    "0xdcbfb530e82f8b12cb284a0a4aa34c7caf317d15": "$HMM",
    "0xdcee5025540b15dcac4f99732b439d9d36866d25": "$AI",
    "0xdd9cdddb4a96a0e66d18e4860ca7195ab8d7c7bc": "$MEME",
    "0xe26d978d4d9b2aa6f2f594880dd415d74055c27d": "$VLAD",
    "0xe55e1642d5e149eb45fd9fda4e7c4e14ce57647e": "$PIPEDOG",
    "0xe781b28e02ed5fc4b989905cb6848d318f4735fd": "$CASHCAT, $TENDIES",
    "0xe7f5641d5eeddb1d8809dd2d2a73d880a3fb91bd": "$BONER",
    "0xe9986545b8c4e7da53344734e386e7747ffb7106": "$HMM",
    "0xeb42372a7b42751f5b67d94993411b3dff689eb9": "$STONKBROKER",
    "0xec4b366a0d29853bb36db07f6c3229ead264ac02": "$PONS",
    "0xed50bdeea8adc232f159486192a4157281d722ff": "$PONS",
    "0xf00d0450982dff5aa2256e88a79476d19212593e": "$VLAD",
    "0xf033364d8c1f89c97fb3888e4f06666a206f1804": "$PONS",
    "0xf7b95fa5c0291319c0d14d098b19ec9d3533fe48": "$MEME",
    "0xfa89ed9d12bf74add8253ddfaa426c4d8a0fa603": "$SLINK",
    "0xfefea9427bef554cc572bc4e887a0b9642fd8f4e": "$MEME",
    "0xff2bcd8e3a12d6930518a45519da1c5e67129948": "$MEME",
}

def skor(n):
    if n >= 3:
        return 7
    if n == 2:
        return 3
    return 1

def bintang(n):
    if n >= 3:
        return "⭐⭐⭐"
    if n == 2:
        return "⭐⭐"
    return "⭐"

def main():
    with open(MASTER, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else [
            "chain", "wallet_normalized", "top10_count", "tokens",
            "meme_ids", "star_level", "score",
        ]
    with open(BACKUP, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    lain = [r for r in rows if r.get("chain", "").strip().lower() != "robinhood"]
    baru = []
    for addr, tokens in RH.items():
        n = len([t for t in tokens.split(",") if t.strip()])
        baru.append({
            "chain": "robinhood",
            "wallet_normalized": addr,
            "top10_count": str(n),
            "tokens": tokens,
            "meme_ids": "",
            "star_level": bintang(n),
            "score": str(skor(n)),
        })
    baru.sort(key=lambda r: (-int(r["score"]), -int(r["top10_count"]), r["wallet_normalized"]))
    semua = lain + baru
    with open(MASTER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(semua)

    hitung = Counter(r["chain"].strip().lower() for r in semua)
    print("Backup:", BACKUP)
    print("Total baris:", len(semua))
    for k, v in sorted(hitung.items()):
        print(k, v)
    print("Robinhood skor7:", sum(1 for r in baru if r["score"] == "7"))
    print("Robinhood skor3:", sum(1 for r in baru if r["score"] == "3"))
    print("Robinhood skor1:", sum(1 for r in baru if r["score"] == "1"))

if __name__ == "__main__":
    main()