# As I like Brownie, stark_brownie 

An interactive CLI wrapper for nile (OZ) and starknet-devnet (Shard-Labs) to help with testing and auditing smart contracts. 

Ultimately this could just be incorporated with nile, however I had started this using starkware testing Starknet Python class, realized 
block and time management would be a pain, so just resorted calling `nile` functions and the `starknet-devnet` API from this tool. 

## How to use 

* Clone this repo inside the folder with contracts to audit/test
* Compile contracts with nile (`nile compile`)
* Launch a `starknet-devnet` node (`nile node`) 
* Launch `stark_brownie.py` and pass the abis path 

## Functionality 

* `call` to call a view function 
* `invoke` to invoke an external function 
* `send` to send a transaction using an account contract 
* `deploy` to deploy a contract
* `declare` to declare a contract class
* `setup` to deploy a contract account -> you will need to set the env variables for them before launching the tool (`export user1=1234`)
* `debug` to debug a tx from its tx_hash 
* `timestamp` to get the timestamp of the block 
* `increase_time` to increase the time of the next block (you can deploy a contract to move to the next block after this)
* `structs` to print all of the structs of a contract 
* `functions` to print all of the functions of a contract
* `hex_to_felt` to convert an hex to a felt
* `str_to_felt` to convert a string to a felt 
* `felt_to_str` to convert a felt to a string 

## Acknowledgments 

This is simply a wrapper around `nile`, so thanks to OpenZeppelin for writing the tool.
Also thanks to Shard-Labs for `starknet-devnet`.
