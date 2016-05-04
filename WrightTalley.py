from collections import defaultdict
from pprint import pprint


# --------
# - Read in the BLT file
# --------

fname = "votes.blt"
fp = open(fname, "r")

auditLog = open("auditLog.txt", "w")

numCandidates, numSeats = (int(x) for x in fp.readline().split(" "))

remainingCandidates = set(range(1, numCandidates + 1)) # Candidate numbers count starting at 1, 0 is the terminator

# If our numbers here on the second line are negative, it means they've withdrawn
intline = [int(x) for x in fp.readline().rstrip().split(" ")]
if intline[0] < 0:
    for failboat in intline:
        remainingCandidates.remove(-failboat)
    intline = [int(x) for x in fp.readline().rstrip().split(" ")]
    
# We're now in the vote block, go 'til we hit a "0" row.
vectors = []
while intline[0] != 0:
    vectors.append([intline[0], intline[1:]])  # [X votes, voteVector]
    intline = [int(x) for x in fp.readline().rstrip().split(" ")]

candidateNames = ["Exhausted"]  # Use candidate 0 as the sentinel for exhausted ballots
for _ in xrange(numCandidates):
    candidateNames.append(fp.readline().rstrip().strip("\n"))

electionName = fp.readline()
fp.close()

# --------
# - Election loopin' time!
# - Outer loop handles resets caused by a candidate being eliminated, resetting vote vectors, quota and winners.
# --------

roundNumber = 1

while len(remainingCandidates) > numSeats:
    auditLog.write("Round %s beginning - %s candidates remain\n" % (roundNumber, len(remainingCandidates), ))
    roundNumber += 1
    winningCandidates = []
    
    # Establish the working copy of the vectors, of the format
    # [remainingWeight, [remainingVector]]
    # filtering out candidates that are no longer in the vote.
    weightedVectors = [[weight, [candidate for candidate in vec if candidate in remainingCandidates]] for weight, vec in vectors]

    # Count up the vectors that have at least one candidate in them in order to form the quota
    electorateSize = 0
    for weight, vector in weightedVectors:
        if vector:
            electorateSize += weight
    droopQuota = int(electorateSize / float(numSeats + 1) + 1)

    candidateEliminated = None
    first = True
    
    # We're going to loop around awarding seats and distributing surpluses until noone is worthy and all the
    # surpluses are distributed.  At that point we eliminate someone, terminate this loop, and restart from the top.
    while candidateEliminated is None and len(winningCandidates) < numSeats:
        # Sum up the top preferences of the current vectors by candidate
        accumulator = defaultdict(float)
        for candidate in remainingCandidates - set(winningCandidates):
            accumulator[candidate] = 0.0
        for weight, vector in weightedVectors:
            if vector:
                accumulator[vector[0]] += weight
        # Listify and sort from most votes to least votes.  Notably, ties are broken here by going to the 2nd
        # element of the tuple and using the candidate index (higher is better).  While not an ideal way to break
        # ties, it's clean and repeatable, while still being random as the candidates are indexed in random order
        # in the .blt file.  This is only unfair if a candidate is involved in two ties, a rather unlikely occurance.
        votesPerCandidate = sorted([(votes, candidate) for candidate, votes in accumulator.iteritems()], reverse=True)

        if first:
            first = False
            pprint([(candidateNames[cand], votes) for votes, cand in votesPerCandidate])
            auditLog.write("%d votes, %d quota\n" % (electorateSize, droopQuota))
            auditLog.write("Initial talley:\n")
            for votes, candidate in votesPerCandidate:
                auditLog.write("  %d %s\n" % (votes, candidateNames[candidate]))
            auditLog.write("Actions:\n")
            
        # First, find newly provisionally elected dudes and remove them from any ballots that have them
        # listed 2nd or further down.  Provisionally elected dudes can't recieve transfer votes (they don't need them either)
        candidatesToRemove = []
        for votes, candidate in [x for x in votesPerCandidate if x[0] >= droopQuota and x[1] not in winningCandidates]:
            print("%s provisionally elected (%s obtained, needed %s)" % (candidateNames[candidate], votes, droopQuota))
            auditLog.write("  Elected: %s\n" % (candidateNames[candidate], ))
            candidatesToRemove.append(candidate)
            winningCandidates.append(candidate)
        for idx, (weight, vector) in enumerate(weightedVectors):
            if vector:
                weightedVectors[idx][1] = [vector[0]] + [cand for cand in vector[1:] if cand not in candidatesToRemove]
        
        # Now, do the vote transfering for the candidate with the highest talley, if they pass quota.
        topVotes, topCandidate = max(votesPerCandidate)
        if topVotes > droopQuota:
            overflowRatio = (topVotes - droopQuota) / topVotes
            print("Transfering from %s, overflow of %s - (%s obtained, needed %s)\n" % (candidateNames[topCandidate], overflowRatio, topVotes, droopQuota))

            # Remove that ratio of weight from any vector that has this candidate as front.  You voted for a winner!
            # Collect up the benefits - that is, the talley of 2nd preferences of voters who currently have the winner
            # as first preference, for auditing purposes.  It's not algorythmically important.
            transferBenefits = defaultdict(float)
            for idx, (weight, vector) in enumerate(weightedVectors):
                if vector and vector[0] == topCandidate:
                    weightedVectors[idx][0] = weight * overflowRatio
                    if len(vector) > 1:
                        transferBenefits[vector[1]] += weight * overflowRatio
                    else:
                        # The vector is exhaused-with-value if the winner was the last candidate listed
                        transferBenefits[0] += weight * overflowRatio
                    
                    # And remove the winner from the front of our vector, transfering it on down.
                    weightedVectors[idx][1] = vector[1:]
                    
            print("Benefitiaries of transfer:")
            benefitiaries = sorted([(votes, cand) for cand, votes in transferBenefits.iteritems()], reverse=True)
            pprint(benefitiaries, width=200)
            
            auditLog.write("  Transfer from %s:\n" % (candidateNames[topCandidate], ))
            auditLog.write("    Votes: %f, Factor: %f, Excess: %f\n" % (topVotes, overflowRatio, topVotes - droopQuota))
            for votes, candidateID in benefitiaries:
                auditLog.write("    %f votes to %s\n" % (votes, candidateNames[candidateID]))
        else:
            # Time to nuke someone, as our top vote-getter did not reach quota
            print("Pre-elimination talley:")
            auditLog.write("  Pre-elimination tally:\n")
            pprint([(candidateNames[cand], votes) for votes, cand in votesPerCandidate])
            for votes, cand in votesPerCandidate:
                auditLog.write("  %d %s\n" % (votes, candidateNames[cand]))
            votes, candidateEliminated = min(votesPerCandidate)
            remainingCandidates.remove(candidateEliminated)
            auditLog.write("  Elimination: %s with %f votes\n\n" % (candidateNames[candidateEliminated], votes))

    if len(winningCandidates) == numSeats:
        # Eliminate everyone else, we've elected enough
        remainingCandidates = set(winningCandidates)

    print("Round over, %s eliminated, %s elected, %s remain\n---------------------------------\n\n" %
            (candidateNames[candidateEliminated] if candidateEliminated else "No one", len(winningCandidates), len(remainingCandidates)))

print("Your council: ")
auditLog.write("Result:\n")
for candidateIdx in sorted(remainingCandidates):
    print(candidateNames[candidateIdx])
    auditLog.write("%s\n" % (candidateNames[candidateIdx]))

auditLog.close()
