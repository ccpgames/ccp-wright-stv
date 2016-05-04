from collections import defaultdict
import random

votes = defaultdict(list)

# Yeah okay apparently it's character IDs.
characterIdToCandidateName = {144925561: "Innominate",
                            164876214: "Rivver",
                            385506955: "Petrified",
                            415026075: "Harry Saq",
                            774017329: "Vaari",
                            986325658: "Wyld",
                            2053796889: "Gorski Car",
                            1991664750: "Niko Lorenzio",
                            962458290: "Aryth",
                            499242457: "Mr Hyde113",
                            665903886: "Brodit",
                            1145376396: "Ed Bever",
                            705026343: "Mining Forman",
                            1545174337: "Sogor",
                            1376900354: "Chiimera",
                            596756116: "Fafer",
                            427312707: "InTheSunset",
                            1664035961: "Viceran Phaedra",
                            344482779: "John Ellsworth",
                            162279905: "Bobmon",
                            646246203: "Xavier Azabu",
                            318420058: "Christy Cloud",
                            1735645598: "Xenuria",
                            639451688: "Apothne",
                            144749738: "Annexe",
                            90212028: "Tora Bushido",
                            90297939: "Iirithine",
                            90357281: "Alner Greyl",
                            90926985: "Steve Ronuken",
                            91235636: "Erika Mizune",
                            91035740: "Diana Olympos",
                            1524496173: "Jin'taan",
                            91696125: "DoToo Foo",
                            91752204: "Kyle Aparthos",
                            91889403: "Sullen Decimus",
                            92207531: "Joffy Aulx-Gao",
                            736517464: "commander aze",
                            92717906: "Vic Jefferson",
                            686125406: "NoobMan",
                            93167961: "Uriel Paradisi Anteovnuecci",
                            94953264: "RF Gnaeus Crassus",
                            93214934: "Kane Carnifex",
                            93227765: "Utari Onzo",
                            93417038: "Capri Sun KraftFoods",
                            93449061: "Falck Longbottom",
                            573001734: "The Judge",
                            92435537: "Jugular Vein",
                            94008109: "Nikolai Agnon",
                            377961586: "Nashh Kadavr",
                            94471524: "Toxic Yaken",
                            94970316: "Borat Guereen",
                            94644678: "Lorelei Ierendi",
                            95479083: "Terandria Starsong"
}

candidates = set(characterIdToCandidateName.keys())

fp = open("votes.csv", "r")

# Expected format:  "voterID, candidateID, voteRank"
for line in fp:
    voterID, candidateID, voteRank, electionid = (x for x in line.split(","))
    candidateID = int(candidateID)
    voteRank = int(voteRank)
    if candidateID not in candidates:
        print("Unknown candidate: %d - entry ignored" % (candidateID, ))
        continue
    votes[voterID].append((voteRank, candidateID))
fp.close()
print("Read %d vectors" % (len(votes), ))

# Assign candidate IDs randomly
ids = range(1, len(candidates) + 1)
random.shuffle(ids)
candidateToID = {charID: str(id) for charID, id in zip(candidates, ids)}
idToCandidate = {id: charID for charID, id in zip(candidates, ids)}

vectors = defaultdict(int)
for voter, votes in votes.iteritems():
    votes = sorted(votes)
    vectors[tuple(candidateToID[x[1]] for x in votes)] += 1

sortedVectors = sorted([(count, vector) for vector, count in vectors.iteritems()], reverse=True)

fp = open("votes.blt", "w")
fp.write("%s 14\n" % (len(candidates), ))
# for vector, count in vectors.iteritems():
for count, vector in sortedVectors:
    fp.write("%d " % (count, ))
    fp.write(" ".join(vector))
    fp.write("\n")
fp.write("0\n")
for idx in xrange(1, len(candidates) + 1):
    fp.write('"' + characterIdToCandidateName[idToCandidate[idx]] + '"\n')
fp.write("CSM 14-seat STV\n")
fp.close()
