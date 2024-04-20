import functools

# from Database import instance as db_instance
from extraction.Semver import Semver

def resolve_semvers(semvers:list[Semver]) -> list[Semver]:
    # Filter out all semvers that are not strictly followups of one of the previous semvers.
    # For exmaple. given [1, 1.1, 2.0, 9.5, 2.2, 2.4, 3], '9.5' should be dropped since it
    # can not be a followup of '1', '1.1', '2.0'. It wouldn't fit anywhere in a version chain
    semvers_valid = [Semver(0)] # Add this, since it can happen that '1.0.0' occurs multiple times
    for i_semver, semver in enumerate(semvers):
        is_followup = any([ semver.is_strict_followup(semver_prev) for semver_prev in semvers_valid ])
        if is_followup: semvers_valid.append(semver)
    # Remove the first semver, since it is just a bootstrapping semver
    semvers_valid = semvers_valid[1:]
    return resolve_semvers_rec(tuple(semvers_valid))

# Cached recursive function
@functools.cache
def resolve_semvers_rec(semvers:tuple[Semver], depth=0):
    semvers = list(semvers)
    """ find the longest possible chain of strictly followup semvers """
    
    # Custom print function, to print the depth of the recursion
    p = lambda *args, **kwargs : print(*tuple([f"[rsr][{str(resolv_i).rjust(3)}]{' | '*depth}"] + list(args)), **kwargs)
    # Filter out semvers that are not followups of the given semver
    chain_filter_non_followup = lambda semver, chain: list(filter(lambda s: s.is_followup(semver), chain))
    # Check if any of the semvers in the chain is a strict followup of the given semver
    chain_is_any_strict_followup = lambda semver, chain: any([ semver.is_strict_followup(s) for s in chain ]) or len(chain) == 0
    # Check if chain a is completely within chain b, by looking at the Semver IDs
    chain_a_in_chain_b = lambda chain_a, chain_b: all([ any([a.id == b_.id for b_ in chain_b]) for a in chain_a ])

    if not len(semvers): return []
    
    # p("Got", semvers)
    
    # Grab semver at the front of the chain
    current_semver = semvers.pop(0)

    # Create a list of all possible followup chains
    followup_chains = []
    for i_semver, semver in enumerate(semvers):
        # If this semver is a strict followup of the current semver
        if semver.is_strict_followup(current_semver):
            # Create a new chain, with this semver at the front
            chain = semvers[i_semver:]
            # Filter out all semvers that are not a followup of this semver
            chain = chain_filter_non_followup(current_semver, semvers[i_semver:] )
            # Filter out all semvers that can't fit anywhere in the chain
            chain_ = []
            for i, s in enumerate(chain):
                if chain_is_any_strict_followup(s, chain_):
                    chain_.append(s)
            # Check if this chain is not already completely within another chain            
            chain_present = any([ chain_a_in_chain_b(chain_, chain) for chain in followup_chains ])
            
            if not chain_present: followup_chains.append( chain_ )

    # for chain in followup_chains: p(f"Next: {chain}")

    # Add all followup chains, prepended with the current semver
    # p("Adding followup chains")
    chains = [ [current_semver] + resolve_semvers_rec(tuple(chain), depth+1) for chain in followup_chains ]
    # Add just the current semver as a possible chain
    # p("Adding current semver")
    chains.append( [current_semver] )
    
    # Ignore the current semver, and add all followup chains
    # First, check if this chain is not already within the previous chains
    if not any([ chain_a_in_chain_b(semvers, chain_) for chain_ in chains ]):
        # p("Ignoring current semver")
        chains.append( resolve_semvers_rec(tuple(semvers), depth+1) )
    
    longest_chain = max(chains, key=len, default=[])
    return longest_chain