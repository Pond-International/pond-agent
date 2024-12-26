# Sybil Address Prediction

Detecting fraudulent blockchain addresses to combat Sybil attacks and enhance the integrity of Web3 projects.

## Overview

In crypto, when a project launches its token, it is very common for the project to send a few tokens to some users for free. This process is called airdrop. Airdrops are a powerful tool for promoting projects and rewarding early adopters. Typically, they allow projects to reward users who have contributed to or consistently used a protocol by distributing free crypto tokens or NFTs. This helps build community engagement and increase participation. 

Normally, a user is only allowed to receive one (or a fixed amount) token in the airdrop. Due to the anonymous nature of blockchain addresses, we don't really know who is behind an address. Hence, some individual may attempt to exploit airdrops by creating multiple addresses to unfairly claim additional tokens. Such behavior is called a Sybil attack.These attacks can harm projects, create unfairness, weaken communities, and undermine trust in the blockchain ecosystem.

There is a more general definition of Sybil attacks where an attacker creates and controls a large number of pseudonymous entities to maliciously influence the blockchain network. Please refer to sybil-attack if you are interested to know more. This competition focuses on the Sybil attack in token airdrops.

The industry needs your expertise! The challenge is to identify blockchain addresses that may be involved in Sybil attacks by analyzing their on-chain activity. By detecting these fraudulent addresses, you can help safeguard the integrity of Web3 projects and support the overall health of the blockchain ecosystem.

If you are unfamiliar with the basic concepts in Crypto such as tokens and wallets, please start with our blog post "Blockchain 101". Otherwise, let's dive in!

## Objective

The objective is to build a machine learning model that predicts whether a given wallet address is associated with Sybil attacks, using historical blockchain data. 

### Model Output
For a given address, assign it to one of two classes:
- 1: Sybil address
- 0: Non-Sybil address

### Data
You are provided a labeled dataset of known Sybil addresses and data on their on-chain activities including their transactions, token transfers, and what tokens they have swapped in decentralized exchanges (DEX). Using this data, you'll need to engineer features and train your model to predict the labels (Sybil or not) of given addresses. How you process the data is up to you—the sky's the limit! Feature engineering, model selection, and optimization are entirely in your hands. If you have no idea where to start, please don’t hesitate to reach out to the competition organizers for an example ML project. 

#### Known Sybil and non-Sybil addresses

A list of Sybil addresses and non-Sybil addresses are provided in the train_addresses table. The non-Sybil addresses are a sample from all addresses. The table contains addresses and their labels (0=non-Sybil, 1=Sybil). 

#### Ethereum Transactions

Historical transactions over the last 10 years for addresses involved in this competition is provided in the transactions table. Each transaction has a unique identifier (TX_HASH), the address initiating the transaction (FROM_ADDRESS), the address being interacted with (TO_ADDRESS), the amount of Ether transacted (VALUE), and other related information. Please see Datasets for details.

#### Transfers of the tokens

ERC-20 token transfers over the past 10 years for wallet addresses in this competition are provided in the token_transfers table. Each transfer inherits data such as block_timestamp and tx_hash from the associated transaction, but also contains parsed data including
- Sending address of the transfer (From_Address) which is not necessarily the same as the From Address of the transaction
- Receiving address of the transfer (To_Address)
- Decimal-adjusted amount of the asset (Amount_Precise) and its USD value (Amount_USD). The USD value is not always available.
- Address of the token being transferred (Contract_Address)

#### DEX swaps of the tokens

Swaps conducted by wallet addresses in this competition on decentralized exchanges over the last 10 years are provided in the dex_swaps table. Each swap inherits data such as block_timestamp and tx_hash from the associated transaction, but also contains parsed data including
- The address of the token sent for swap (Token_In)
- The address of the token being swapped to (Token_Out)
- Amount of input token (Amount_In) and its USD value (Amount_In_USD)
- Amount of token received (Amount_Out) and its USD value (Amount_Out_USD)
- The address that initiate the swap (Origin_From_Address)
- The address that receives the swapped token (TX_TO)

## Evaluation

A test set of addresses is provided in the test_addresses table. For each address in the test set, please classify it into one of two classes: 0 (non-sybil) or 1 (sybil). The predicted labels will be compared with the ground truth labels we have. The following metric will be assessed.
- **Accuracy**: The overall percentage of correctly classified addresses. If your predicted label matches the true label, you score a point! The mathematical formula is:
    
    $$
    accuracy = 1/n \sum 1(y^*_i=y_i)
    $$
    
where *n* is the number of addresses,  $y^*_i$ is the true label for address *i* and $y_i$ is your predicted label.

## Submission File

Once your model is ready, submit your predictions for the test addresses in a simple CSV file with two columns (The column names have to match below exactly or the evaluation will error out): 
- ADDRESS: Wallet addresses from the test set.
- PRED: Your predicted labels (0 or 1). 

Make sure to submit predictions for every address in the test set, as any missing predictions will be counted as incorrect.