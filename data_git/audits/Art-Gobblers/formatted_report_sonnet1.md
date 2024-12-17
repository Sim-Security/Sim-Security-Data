Here is the reformatted audit report following the specified formatting rules:

# Art Gobblers Security Review

## Auditors

- Kurt Barry, Lead Security Researcher
- Leo Alt, Lead Security Researcher  
- Hari, Lead Security Researcher
- Emanuele Ricci, Security Researcher
- Patrickd, Security Researcher
- Hrishikesh Bhat, Apprentice
- Devansh Batham, Apprentice
- Alex Beregszaszi, Consultant

## About Spearbit

Spearbit is a decentralized network of expert security engineers offering reviews and other security related services to Web3 projects with the goal of creating a stronger ecosystem. Our network has experience on every part of the blockchain technology stack, including but not limited to protocol design, smart contracts and the Solidity compiler. Spearbit brings in untapped security talent by enabling expert freelance auditors seeking flexibility to work on interesting projects together.

Learn more about us at spearbit.com

## Introduction

Art Gobblers is an NFT art factory & gallery owned by an exclusive group of users. Gobblers are animated characters with generative attributes on which project users can draw, feed art to & generate tokens. The Art Gobblers project aims to become a nexus point for artists, collectors, and crypto enthusiast over time.

*Disclaimer*: This security review does not guarantee against a hack. It is a snapshot in time of Art Gobblers according to the specific commit. Any modifications to the code will require a new security review.

## Risk Classification

| Severity level | Impact: High | Impact: Medium | Impact: Low |
|----------------|---------------|-----------------|--------------|
| Likelihood: high | Critical | High | Medium |
| Likelihood: medium | High | Medium | Low |
| Likelihood: low | Medium | Low | Low |

### Impact

- High leads to a loss of a significant portion (>10%) of assets in the protocol, or significant harm to a majority of users.
- Medium global losses <10% or losses to only a subset of users, but still unacceptable.
- Low losses will be annoying but bearable--applies to things like griefing attacks that can be easily repaired or even gas inefficiencies.

### Likelihood

- High almost certain to happen, easy to perform, or not easy but highly incentivized
- Medium only conditionally possible or incentivized, but still relatively likely
- Low requires stars to align, or little-to-no incentive

### Action required for severity levels

- Critical Must fix as soon as possible (if already deployed)
- High Must fix (before deployment if not already deployed)
- Medium Should fix
- Low Could fix

## Executive Summary

Over the course of 12 days in total, Art Gobblers engaged with Spearbit to review Art-Gobblers. In this period of time a total of 23 issues were found.

#### Summary

| Project Name | Art Gobblers |
|--------------|--------------|
| Repository | art-gobblers |
| Commit | fe647c8a7e45... |
| Type of Project | Art, NFT |
| Audit Timeline | July 4th - July 15th |
| Methods | Manual Review |

#### Issues Found

| Critical Risk | 0 |
|----------------|---|
| High Risk | 0 |  
| Medium Risk | 0 |
| Low Risk | 3 |
| Gas Optimizations | 4 |
| Informational | 16 |
| Total Issues | 23 |

## Findings

### Low Risk

#### [The claimGobbler function does not enforce the MINTLIST_SUPPLY on-chain](#finding-5.1.1)

**Severity:** Low

**Context:** ArtGobblers.sol#L287-L304

**Description:**  
There is a public constant MINTLIST_SUPPLY (2000) that is supposed to represent the number of gobblers that can be minted by using merkle proofs. However, this is not explicitly enforced in the claimGobbler function and will need to be verified off-chain from the list of merkle proof data.

The risk lies in the possibility of having more than 2000 proofs.

**Recommendation:**  
Consider implementing the following recommendations.

1. The check can be enforced on-chain by adding a state variable to track the number of claims and revert if there are more than MINTLIST_SUPPLY number of claims. However, this adds a state variable which needs to be updated on each claim, thereby increasing gas costs. It is understandable if such suggestion is not implemented due to gas concerns.
2. Alternatively, publish the entire merkle proof data so that anyone can verify off-chain that it contains at most 2000 proofs.

**Resolution:**  
Documented this in ArtGobblers.sol#L335.

```
/// @dev Function does not directly enforce the MINTLIST_SUPPLY limit for gas efficiency. The
/// limit is enforced during the creation of the merkle proof, which will be shared publicly.
```

#### [Feeding a gobbler to itself may lead to an infinite loop in the off-chain renderer](#finding-5.1.2)

**Severity:** Low

**Context:** ArtGobblers.sol#L653

**Description:**  
The contract allows feeding a gobbler to itself and while we do not think such action causes any issues on the contract side, it will nevertheless cause potential problems with the off-chain rendering for the gobblers.

The project explicitly allows feeding gobblers to other gobblers. In such cases, if the off-chain renderer is designed to render the inner gobbler, it would cause an infinite loop for the self-feeding case.

Additionally, when a gobbler is fed to another gobbler the user will still own one of the gobblers. However, this is not the case with self-feeding,.

**Recommendation:**  
Consider implementing the following recommendations.

1. Disallowing self-feeding.
2. If self-feeding is allowed, the off-chain renderer should be designed to handle this case so that it can avoid an infinite loop.

**Resolution:**  
Fixed in commit fa81257.

**Spearbit:** Acknowledged.

#### [The function toString() does not manage memory properly](#finding-5.1.3)

**Severity:** Low

**Context:** LibString.sol#L7-L72

**Description:**  
There are two issues with the toString() function:

1. It does not manage the memory of the returned string correctly. In short, there can be overlaps between memory allocated for the returned string and the current free memory.
2. It assumes that the free memory is clean, i.e., does not explicitly zero out used memory.

Proof of concept for case 1:

```solidity
function testToStringOverwrite() public {
    string memory str = LibString.toString(1);
    uint freememptr;
    uint len;
    bytes32 data;
    uint raw_str_ptr;
    assembly {
        // Imagine a high level allocation writing something to the current free memory.
        // Should have sufficient higher order bits for this to be visible
        mstore(mload(0x40), not(0))
        freememptr := mload(0x40)
        // Correctly allocate 32 more bytes, to avoid more interference
        mstore(0x40, add(mload(0x40), 32))
        raw_str_ptr := str
        len := mload(str)
        data := mload(add(str, 32))
    }
    emit log_named_uint("memptr: ", freememptr);
    emit log_named_uint("str: ", raw_str_ptr);
    emit log_named_uint("len: ", len);
    emit log_named_bytes32("data: ", data);
}
Logs:
```
memptr: : 256 str: : 205 len: : 1 data: : 0x31000000000000000000000000000000000000ffffffffffffffffffffffffff

The key issue here is that the function allocates and manages memory region [205, 269) for the return variable. However, the free memory pointer is set to 256. The memory between [256, 269) can refer to both the string and another dynamic type that's allocated later on.

Proof of concept for case 2:

```solidity
function testToStringDirty() public {
    uint freememptr;
    // Make the next 4 bytes of the free memory dirty
    assembly {
        let dirty := not(0)
        freememptr := mload(0x40)
        mstore(freememptr, dirty)
        mstore(add(freememptr, 32), dirty)
        mstore(add(freememptr, 64), dirty)
        mstore(add(freememptr, 96), dirty)
        mstore(add(freememptr, 128), dirty)
    }
    string memory str = LibString.toString(1);
    uint len;
    bytes32 data;
    assembly {
        freememptr := str
        len := mload(str)
        data := mload(add(str, 32))
    }
    emit log_named_uint("str: ", freememptr);
    emit log_named_uint("len: ", len);
    emit log_named_bytes32("data: ", data);
    assembly {
        freememptr := mload(0x40)
    }
    emit log_named_uint("memptr: ", freememptr);
}
```

```
Logs: str: 205 len: : 1 data: : 0x31ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff memptr: : 256
```

In both cases, high level solidity will not have issues decoding values as this region in memory is meant to be empty. However, certain ABI decoders, notably Etherscan, will have trouble decoding them.

Note: It is likely that the use of toString() in ArtGobblers will not be impacted by the above issues. However, these issues can become severe if LibString is used as a generic string library.

**Recommendation:**  
For the first case, we recommend allocating 160 bytes rather than 128 bytes in LibString.sol#L22.

```solidity
- mstore(0x40, add(str, 128))
+ mstore(0x40, add(str, 160))
```
For the second case, the easiest fix would be to zero out the memory that follows the final character in the string.

**Resolution:**  
The suggestions (1) and (2) are implemented in LibString.sol from Solmate.

**Spearbit:** Acknowledged.

### Gas Optimization

#### [Consider migrating all require statements to Custom Errors for gas optimization, better UX, DX and code consistency](#finding-5.2.1)

**Severity:** Gas Optimization

**Context:** ArtGobblers.sol, SignedWadMath.sol, GobblersERC1155B.sol, PagesERC721.sol

**Description:**  
There is a mixed usage of both require and Custom Errors to handle cases where the transaction must revert.

We suggest replacing all require instances with Custom Errors in order to save gas and improve user / developer experience.

The following is a list of contract functions that still use require statements:

- ArtGobblers mintLegendaryGobbler
- ArtGobblers safeBatchTransferFrom
- ArtGobblers safeTransferFrom
- SignedWadMath wadLn
- GobblersERC1155B balanceOfBatch
- GobblersERC1155B _mint
- GobblersERC1155B _batchMint
- PagesERC721 ownerOf
- PagesERC721 balanceOf
- PagesERC721 approve
- PagesERC721 transferFrom
- PagesERC721 safeTransferFrom
- PagesERC721 safeTransferFrom (overloaded version)

**Recommendation:**  
Consider replacing all instances of the require statement with Custom Errors across the codebase.

#### [Minting of Gobbler and Pages can be further gas optimized](#finding-5.2.2)

**Severity:** Gas Optimization

**Context:** Pages.sol#L126-L143, ArtGobblers.sol#L310-L331

**Description:**  
Currently, in order to mint a new Page or Gobbler users must have enough $GOO in their Goo contract balance. If the user does not have enough $GOO he/she must call ArtGobblers.removeGoo(amount) to remove the required amount from the Gobbler's balance and mint new $GOO. That $GOO will be successively burned to mint the Page or Gobbler.

In the vast majority of cases users will never have $GOO in the Goo contract but will have their $GOO directly stacked inside their Gobblers to compound and maximize the outcome.

Given these premises, it makes sense to implement a function that does not require users to make two distinct transactions to perform:

- mint $GOO (via removeGoo).
- burn $GOO + mint the Page/Gobbler (via mintFromGoo).

but rather use a single transaction that consumes the $GOO stacked on the Gobbler itself without ever minting and burning any $GOO from the Goo contract. By doing so, the user will perform the mint operation with only one transaction and the gas cost will be much lower because it does not require any interaction with the Goo contract.

**Recommendation:**  
Consider evaluating the possibility to allow users mint Gobbler's and Page's directly from the $GOO balance in ArtGobbler to save gas.

**Resolution:**  
Recommendation implemented in PR 113.

**Spearbit:** Acknowledged.

#### [Declare GobblerReserve artGobblers as immutable](#finding-5.2.3)

**Severity:** Gas Optimization

**Context:** GobblerReserve.sol#L17

**Description:**  
The artGobblers in the GobblerReserve can be declared as immutable to save gas.

```solidity
- ArtGobblers public artGobblers;
+ ArtGobblers public immutable artGobblers;
```

**Recommendation:**  
Declare the artGobblers variable as immutable.

**Resolution:**  
Recommendation implemented in the PR 111.

**Spearbit:** Acknowledged.

### Informational

#### [Neither GobblersERC1155B nor ArtGobblers implement the ERC-165 supportsInterface function](#finding-5.3.1)

**Severity:** Informational

**Context:** ArtGobblers.sol, GobblersERC1155B.sol

**Description:**  
From the EIP-1155 documentation:

*Smart contracts implementing the ERC-1155 standard MUST implement all of the functions in the ERC1155 interface. Smart contracts implementing the ERC-1155 standard MUST implement the ERC-165 supportsInterface function and MUST return the constant value true if 0xd9b67a26 is passed through the interfaceID argument.*

Neither GobblersERC1155B nor ArtGobblers are actually implementing the ERC-165 supportsInterface function.

**Recommendation:**  
Consider implementing the required ERC-165 supportsInterface function in the GobblersERC1155B contract.

**Resolution:**  
Implemented in GobblersERC1155B.sol#L124 and PagesERC721.sol#L162.

**Spearbit:** Acknowledged.

#### [LogisticVRGDA is importing wadExp from SignedWadMath but never uses it](#finding-5.3.2)

**Severity:** Informational

**Context:** LogisticVRGDA.sol#L4

**Description:**  
The LogisticVRGDA is importing the wadExp function from the SignedWadMath library but is never used.

**Recommendation:**  
Remove the wadExp to improve readability.

```solidity
-import {wadExp, wadLn, unsafeDiv, unsafeWadDiv} from "../lib/SignedWadMath.sol";
+import {wadLn, unsafeDiv, unsafeWadDiv} from "../lib/SignedWadMath.sol";
```

**Resolution:**  
Recommendation implemented in the PR 111.

**Spearbit:** Acknowledged.

#### [Pages.tokenURI does not revert when pageId is the ID of an invalid or not minted token](#finding-5.3.3)

**Severity:** Informational

**Context:** Pages.sol#L207-L211

**Description:**  
The current implementation of tokenURI in Pages is returning an empty string if the pageId specified by the user's input has not been minted yet (pageId > currentId).

Additionally, the function does not correctly handle the case of a special tokenId equal to 0, which is an invalid token ID given that the first mintable token would be the one with ID equal to 1.

The EIP-721 documentation specifies that the contract should revert in this case:

*Throws if _tokenId is not a valid NFT. URIs are defined in RFC 3986.*

**Recommendation:**  
When the specified pageId has not been