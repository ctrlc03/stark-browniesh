import requests
from utils import (
    from_uint,
    str_to_felt,
    to_uint,
    felt_to_str,
    out,
    banner,
    Interface
)
import asyncio
import json 
import readline
from tabulate import tabulate 
import argparse 
import os

# parser options 
parser = argparse.ArgumentParser(description='StarkBrownie')
parser.add_argument('--abi_folder', type=str, help="The folder containing the contracts abi", default="artifacts/abis/")
parser.add_argument('--contract_dir', type=str, help="The path to the contract directory", default="contracts/")

contract_declarations = []
contract_addresses = []
account_contracts = []

global abis
abis = {}
global structs
structs = {}
global contracts_functions 
contracts_functions = {}
global account_counter
account_counter = 1
global output
output = Interface()
global struct_names
struct_names = []

# get cli options
# unused for now 
def get_options():
    args = parser.parse_args()
    return args.abi_folder, args.contract_dir


# convert hex to felt 
def hex_to_felt(value):
    return int(value, 16)

global options 
options = []
    
# readline function 
def completer(text, state):
    global options 
    option = [x for x in options if x.startswith(text)]
    try:
        return option[state]
    except IndexError:
        return None 

# set the completer stuff
readline.set_completer(completer)
readline.parse_and_bind("tab: complete")

# invoke a function with no wallet 
def nile_invoke(contract_alias, function_name, args):
    to_pass = "nile invoke " + contract_alias + ' ' + function_name + ' ' 
    for arg in args:
        for key, val in arg.items():
            if val == 'Uint256':                
                to_pass = to_pass + str(key[0]) + ' ' + str(key[1]) + ' '
            else:
                to_pass = to_pass + str(key) + ' '

    code, res, err = out(to_pass)
    if code == 0:
        if res == '':
            output.greenn(err)
        else:
            output.greenn(res)
    else:
        output.redd(err)  

# call a view function and get the output 
def nile_call(contract_alias, function_name, args):
    to_pass = "nile call " + contract_alias + ' ' + function_name + ' ' 
    for arg in args:
        for key, val in arg.items():
            if val == 'Uint256':
                to_pass = to_pass + str(key[0]) + ' ' + str(key[1]) + ' '
            else:
                to_pass = to_pass + str(key) + ' '

    code, res, err = out(to_pass)
    outputs_types = get_function_outputs_from_contract_and_function_name(contract_alias, function_name)

    if code == 0:
        if res == '':
            err_splitted = err.split(" ")
            if len(outputs_types) > 0:
                print()
                counter = 0
                for out_type in outputs_types:
                    output.info(str(out_type['name']) + ' (' + str(out_type['type']) + ")\n")
                    struct_data = get_struct_data_from_source_and_name(contract_alias, out_type['type'])
                    if struct_data:
                        for _, value in struct_data.items():
                            for key, val in value.items():
                                output.greenn(str(key) + " (" +  str(val) + ") " + "--> " +  str(err_splitted[counter]))
                                counter+=1 
                    else:
                        for res_ in res_splitted:
                            output.greenn(str(res_))
        else:
            res_splitted = res.split(" ")
            if len(outputs_types) > 0:
                print()
                counter = 0
                for out_type in outputs_types:
                    output.info(str(out_type['name']) + ' (' + str(out_type['type']) + ")\n")
                    struct_data = get_struct_data_from_source_and_name(contract_alias, out_type['type'])
                    if struct_data:
                        for _, value in struct_data.items():
                            for key, val in value.items():
                                output.greenn(str(key) + " (" +  str(val) + ") " + "--> " +  str(res_splitted[counter]))
                                counter+=1 
                    else:
                        for res_ in res_splitted:
                            output.greenn(str(res_))
    else:
        output.redd(err)    

# deploy a contract
def nile_deploy(contract_alias, args):
    to_pass = "nile deploy " + contract_alias + " "
    for arg in args:
        to_pass = to_pass + str(arg) 
    to_pass = to_pass + ' --alias ' + str(contract_alias)
    global contract_addresses

    code, res, err = out(to_pass)
    print()

    if code == 0:
        if res == '':
            output.greenn(err)
            splitted = err.splitlines()[1]
            contract_addresses.append({contract_alias: splitted.split(" ")[-1]})
        else:
            output.greenn(res)
            splitted = res.splitlines()[1]
            contract_addresses.append({contract_alias: splitted.split(" ")[-1]})
        options.append(contract_alias)
        output.info("If a proxy contract, go and change the abi to point to the implementation on localhost.deployments.txt")
    else:
        output.redd(err)     

# declare a contact class 
def nile_declare(contract_alias):
    output.info("Declaring " + str(contract_alias) + ' --alias ' + str(contract_alias) + "\n")
    code, res, err = out('nile declare ' + contract_alias + ' --alias ' + contract_alias)
    global contract_declarations
    if code == 0:
        if res == '':
            output.greenn(err)
            splitted = err.splitlines()[1]
            contract_declarations.append({contract_alias: splitted.split(" ")[-1]})
        else:
            output.greenn(res)
            splitted = res.splitlines()[1]
            contract_declarations.append({contract_alias: splitted.split(" ")[-1]})
        options.append(contract_alias)
    else:
        output.redd(err)       

# setup an account contract 
def nile_setup(alias):
    global account_counter 
    global account_contracts
    
    output.info("Deploying an account contract with alias " + alias + "\n")
    code, res, err = out('nile setup ' + alias) 

    if code == 0:
        if res == '':
            output.greenn(err)
            splitted = err.splitlines()[1]
            account_contracts.append({alias: splitted.split(" ")[-1]})
        else:
            output.greenn(res)
            splitted = res.splitlines()[1]
            account_contracts.append({alias: splitted.split(" ")[-1]})
        options.append(alias)
    else:
        output.redd(err)   

# debug a tx via its hash 
def nile_debug(tx_hash):
    code, res, err = out('nile debug ' + tx_hash)
    print()
    if code == 0:
        if res == '':
            output.greenn(err)
        else:
            output.greenn(res)
    else:
        output.redd(err)   

# get all of the args we need to send a function 
def request_args(contract, function):
    function_data = get_function_inputs_from_contract_and_function_name(contract, function)   
    args = []
    try:
        if len(function_data) > 0:
            for argument in function_data: # now we have a dict
                struct_data = get_struct_data_from_source_and_name(contract, argument['type'])
                if struct_data:
                    if argument['type'] == "Uint256":
                        tmp_input = int(input("stark_brownie#> " + argument['name'] + ' (' + str(argument['type']) + ') '))
                        tmp_input = to_uint(tmp_input)
                        args.append({tmp_input: argument['type']})
                    else:
                        for _, members in struct_data.items():
                            for member, value in members.items():
                                output.info(argument['name'] + ' (' + str(argument['type']) + ')')
                                tmp_input = input("stark_brownie#> " + member + " (" + value + ") ") 
                                if value == "felt":
                                    if len(tmp_input) == 66:
                                        tmp_input = hex_to_felt(tmp_input)
                                    elif not tmp_input.isnumeric():
                                        tmp_input = str_to_felt(tmp_input)                            
                                args.append({tmp_input: value})    
                else:
                    tmp_input =  input("stark_brownie#> " + argument['name'] + " (" + argument['type'] + ") ")
                    if argument['type'] == "felt":
                        if len(tmp_input) == 66:
                            tmp_input = hex_to_felt(tmp_input)
                        elif tmp_input.startswith("0x") and len(tmp_input) == 65:
                            new_string = tmp_input[:2] + "0" + tmp_input[2:]
                            tmp_input = hex_to_felt(new_string)
                        elif not tmp_input.isnumeric(): # hex account can be 66 or 65 if you omit the 0 after 0x
                            tmp_input = str_to_felt(tmp_input)
                    elif argument['type'] == "Uint256":
                        tmp_input = to_uint(int(tmp_input))
                    elif argument['type'] == "felt*":
                        my_temp = tmp_input.split(" ")
                        tmp_input = ""
                        for tmp in my_temp:
                            if len(tmp) == 66:
                                tmp_input = tmp_input + str(hex_to_felt(tmp))
                            elif not tmp_input.isnumeric():
                                tmp_input = tmp_input + str(str_to_felt(tmp_input))
                            else:
                                tmp_input = tmp_input + str(int(tmp_input))
                    args.append(
                        {
                            tmp_input : argument['type']
                        }
                    )
        return args 
    except Exception as e:
        output.redd(str(e))
        return args 

# send a transaction using a contract account
def nile_send(user_alias, contract_alias, function_name, args):
    to_pass = "nile send " + user_alias + ' ' + contract_alias + " " + function_name + ' '
    for arg in args:
        for key, val in arg.items():
            if val == 'Uint256':
                to_pass = to_pass + str(key[0]) + ' ' + str(key[1]) + ' '
            else:
                to_pass = to_pass + str(key) + ' '

    code, res, err = out(to_pass)

    if code == 0:
        if res == '':
            output.greenn(err)
        else:
            output.greenn(res)
    else:
        output.redd(err)   

# Load local accounts
def load_accounts():
    global account_contracts
    global account_counter
    if os.path.exists('localhost.accounts.json'):
        output.info("Loading contract accounts")
        accounts_data = None 

        with open('localhost.accounts.json', 'r') as in_file:
            accounts_data = in_file.readlines() 
        for line in accounts_data:
            splitted = line.split(":")
            account_contracts.append({'account' + str(account_counter) : splitted[0]})
            options.append('account-' + str(account_counter))
            account_counter += 1 

# Load already deployed contracts
def load_contracts():
    global contract_addresses

    if os.path.exists('localhost.deployments.txt'):
        output.info("Loading contracts")
        contract_data = None 

        with open('localhost.deployments.txt', 'r') as in_file:
            contract_data = in_file.readlines() 
        for line in contract_data:
            splitted = line.split(":")
            account_contracts.append({splitted[-1] : splitted[0]})
            options.append(splitted[0])

# increase the time of the next block 
def increase_time(timestamp):
    url = 'http://127.0.0.1:5050/set_time'
    headers = {'Content-Type': 'application/json'}
    data = {'time': timestamp}
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code == 200:
        print()
        output.greenn("Increased next block timestamp to " + str(timestamp))
    else:
        print()
        output.redd("There was an error")

# get the current block numebr 
def get_block_number():
    url = 'http://127.0.0.1:5050/rpc'
    data = {"jsonrpc": "2.0", "method": "starknet_blockNumber", "params": [], "id": 0}
    headers = {'Content-Type': "application/json"}
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code == 200:
        data = json.loads(resp.text)
        return data['result'] 

# get the current timestamp 
def get_timestamp():
    url = 'http://127.0.0.1:5050/rpc'
    data =  {"jsonrpc": "2.0", "method": "starknet_getBlockByNumber", "params": {"block_number": get_block_number()}, "id": 0}
    headers = {'Content-Type': "application/json"}
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code == 200:
        data = json.loads(resp.text)
        print()
        output.greenn(data['result']['timestamp'])
    else:
        output.redd("Failed to get the current timestamp")

# print the contracts that have been deployed so far
def print_contracts():
    with open('localhost.deployments.txt', 'r') as in_file:
        for line in in_file:
            splitted = line.split(":")
            output.greenn(str(splitted[0]) + ' --> ' + str(splitted[-1]))

# load abi from a dir or form one file 
def load_abi(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            for filename in os.listdir(path):
                try:
                    with open(os.path.join(path, filename), 'r') as f:
                        abis[filename.split("/")[-1].split(".")[0]] = json.load(f)
                        load_contract_functions(filename.split("/")[-1].split(".")[0])
                except Exception:
                    pass 
            pass 
        else:
            with open(path, 'r') as f:
                abis[path.split("/")[-1].split(".")[0]] = json.load(f)
                load_contract_functions(path.split("/")[-1].split(".")[0])
        parse_structs_from_abi()
    else:
        output.error("The path does not exist")
        exit(1)

# parse the structs from abi 
def parse_structs_from_abi():
    # global structs
    for key, value in abis.items():
        data = {}
        for item in value:
            if item['type'] == "struct":
                member_data = {}
                struct_names.append([item['name']])
                for member in item['members']:
                    member_data[member['name']] = member['type']
                data[item['name']] = member_data
        structs[key] = data    

# get the struct data
def get_struct_data_from_source_and_name(contract_name, struct_name):
    try:
        data = {}
        for struct, struct_data in structs[contract_name].items():   
            if struct == struct_name:
                data[struct_name] = struct_data
        return data 
    except KeyError:
        output.redd("There is no contract " + contract_name)
        return {}

# Load all functions and data from a contract
def load_contract_functions(contract_name):
    try:
        all_functions = []
        for entry in abis[contract_name]:
            if entry['type'] == "function":
                if entry['name'] is not None:
                    all_functions.append(entry)
                    options.append(entry['name'])
        contracts_functions[contract_name] = all_functions
    except KeyError:
        output.redd("There is no contract " + contract_name) 

# get a contract function's names
def get_contract_functions_name(contract_name):
    try:
        all_functions = {}
        for entry in abis[contract_name]:
            if entry['type'] == "function":
                if entry['name'] is not None:
                    all_functions[contract_name] = entry['name']
        return all_functions
    except KeyError:
        output.redd("There is not contract " + contract_name)
        return []

# get the outputs of a function 
def get_function_outputs_from_contract_and_function_name(contract_name, function_name):
    try:
        for function in contracts_functions[contract_name]:
            if function['name'] == function_name:
                return function['outputs']
        return []
    except KeyError:
        output.redd("There is no contract " + contract_name)
        return []

# get the inputs for a function 
def get_function_inputs_from_contract_and_function_name(contract_name, function_name):
    try:
        for function in contracts_functions[contract_name]:
            if function['name'] == function_name:
                return function['inputs']
        return []
    except KeyError:
        output.redd("There is no contract " + contract_name)
        return []


# print contract functions for a contract
def print_contract_functions_from_name(contract_name):
    try:
        data = []
        for function in contracts_functions[contract_name]:
            if function['type'] == "function":
                tmp_data = []
                tmp_data.append(function['name'])
                if len(function['inputs']) > 0:
                    tmp_input = ""
                    for input_args in function['inputs']:
                        tmp_input = tmp_input + input_args['name'] + " (" + input_args['type'] + ")\n"
                    tmp_data.append(tmp_input)
                else:
                    tmp_data.append("None")
                if len(function['outputs']) > 0:
                    tmp_output = ""
                    for output_data in function['outputs']:
                        tmp_output = tmp_output + output_data['name'] + " (" + output_data['type'] + ")\n"
                    tmp_data.append(tmp_output)
                else:
                    tmp_data.append("None")
                if 'stateMutability' in function:
                    tmp_data.append(function['stateMutability'])
                else:
                    tmp_data.append("external")
                data.append(tmp_data)
        print(tabulate(data, ["Name", "Input", "Output", "Mutability"], tablefmt="fancy_grid"))
    except KeyError:
        output.redd("There is no function data for contract " + contract_name)

# print structs data for a contract
def print_structs_from_name(contract_name):
    try:
        print_data = []
        for struct, data in structs[contract_name].items():
            tmp_member = ""
            for key, members in data.items():
                tmp_member = tmp_member + key + " (" + members + ")\n" 
            print_data.append([struct, tmp_member])
        print()
        if len(print_data) > 0:
            print(tabulate(print_data, ["Name", "Member"], tablefmt="fancy_grid")) 
        else:
            output.info("There are no structs in the contract " + str(contract_name))
    except KeyError:
        output.redd("There is no contract " + contract_name)

# our main function
async def main():
    # print the banner 
    banner()

    output.info("Make sure starknet-devnet is running (nile node)")

    # print stuff related to the account contracts
    output.info('Unfortunately you have to set accounts private keys as env variables before running the script')
    output.info('export user1=1234 before using the (send) command')
    output.info('export user2=5678')
    output.info('export user3=5738\n\n')

    output.warning("If you deploy a proxy contract, make sure you set the alias to be the one of the implementation contract\n")

    # get the abis dir 
    abi_path = input("stark_brownie#> (select a file to load the abi from or a directory) ")
    load_abi(abi_path)

    global options 

    # append our options 
    options.append('help')
    options.append('setup')
    options.append('invoke')
    options.append('call')
    options.append('send')
    options.append('deploy')
    options.append('declare')
    options.append('hex_to_str')
    options.append('str_to_felt')
    options.append('hex_to_felt')
    options.append('felt_to_str')
    options.append('functions')
    options.append('structs')
    options.append('timestamp')
    options.append('increase_time')
    options.append('print_contracts')
    options.append('load_abi')

    print()
    output.info("Loading the abi in the folder artifacts/abi")
    output.info("Parsing the custom structs of the contracts in the artifacs/abi folder")
    # load cached contracts and acconts 
    load_accounts()
    load_contracts()

    # get cli options (not used for now)
    abi_dir, contract_dir = get_options()

    print()

    # main cli loop 
    while True:
        try:
            # get the options 
            mode = input("stark_brownie#> ").strip()
            print()
            # have fun 
            try:
                if mode == "send":
                    contract = input("stark_brownie#> (contract) ")
                    function_name = input("stark_brownie#> (function_name) ")
                    if function_name not in options:
                        output.warning("This function does not exist\n")
                        continue 
                    arguments = request_args(contract, function_name)
                    user_alias = input("stark_brownie#> (calling user_alias) ")
                    print()
                    nile_send(user_alias, contract, function_name, arguments)
                    print()
                    continue 
                elif mode == "invoke":
                    contract = input("stark_brownie#> (contract) ")
                    function_name = input("stark_brownie#> (function_name) ")
                    if function_name not in options:
                        output.warning("This function does not exist\n")
                        continue 
                    arguments = request_args(contract, function_name)
                    print()
                    nile_invoke(contract, function_name, arguments)
                    continue 
                elif mode == "call":
                    contract = input("stark_brownie#> (contract) ")
                    function_name = input("stark_brownie#> (function_name) ")
                    if function_name not in options:
                        output.warning("This function does not exist\n")
                        continue 
                    arguments = request_args(contract, function_name)
                    print()
                    nile_call(contract, function_name, arguments)
                    continue 
                elif mode == "deploy":
                    alias = input("stark_brownie#> (Alias) ")
                    contract_arguments = input("stark_brownie#> Contract arguments (same line) ")
                    print()
                    nile_deploy(alias, contract_arguments)
                    continue 
                elif mode == "declare":
                    alias = input("stark_brownie#> (Alias) ")
                    print()
                    nile_declare(alias)
                    continue 
                elif mode == "functions":
                    contract_name = input("stark_brownie#> (contract_name) ")
                    print_contract_functions_from_name(contract_name)
                elif mode == "debug":
                    tx_hash = input("stark_brownie#> (tx_hash) ")
                    nile_debug(tx_hash)
                    print()
                    continue
                elif mode == "setup":
                    # private_key = input("stark_brownie#> (Private key) ")
                    alias = input("stark_brownie#> Alias ")
                    print()
                    nile_setup(alias)
                    continue 
                elif mode == "increase_time":
                    output.info("Don't increase too much or you'll break it")
                    print()
                    new_timestamp = int(input("stark_brownie#> (new_timestamp) "))
                    increase_time(new_timestamp)
                    print()
                    continue
                elif mode == "timestamp":
                    get_timestamp()
                    print()
                    continue  
                elif mode == "structs":
                    contract_name = input("stark_brownie#> (contract_name) ")
                    print_structs_from_name(contract_name)
                    print()
                    continue
                elif mode == "print_contracts":
                    print_contracts()
                    continue 
                elif mode == "from_uint":
                    to_convert_low = int(input("stark_brownie#> (low) "))
                    to_convert_high = int(input("stark_brownie#> (high) "))
                    output.green(str(from_uint((to_convert_low, to_convert_high))))
                    continue
                elif mode == "load_abi":
                    path = input("stark_brownie#> (enter path) ")
                    load_abi(path)
                    print()
                    continue 
                elif mode == "help":
                    print(tabulate([["functions", "Print all the functions and their types"], ["functions_name", "Print functions names"],
                        ["structs", "Print structs and their members"], ["structs_name", "Print structs names"], 
                        ["help", "Display this menu"],
                        ["str_to_felt", "Converts a string to felt"],
                        ["felt_to_str", "Converts a felt to string"],
                        ["hex_to_felt", "Converts an hex to a felt"],
                        ["from_uint", "Convert to felt from Uint256"]], 
                        ["Option", "Description"], tablefmt="fancy_grid"))
                    continue
                elif mode == "str_to_felt":
                    to_convert = input("stark_brownie#> (enter string) ")
                    print()
                    output.greenn(str_to_felt(to_convert))
                    continue 
                elif mode == "hex_to_felt":
                    to_convert = input("stark_brownie#> (enter hex) ")
                    print()
                    output.greenn(hex_to_felt(to_convert))
                    continue 
                elif mode == "felt_to_str":
                    to_convert = int(input("stark_brownie#> (enter felt) "))
                    print()
                    output.greenn(felt_to_str(to_convert))
                    continue 
                elif mode == "hex_to_str":
                    to_convert = input("stark_brownie#> (enter hex) ")
                    print()
                    if to_convert[:2] == "0x":
                        output.greenn(bytes.fromhex(to_convert[2:]).decode('utf-8'))
                    print() 
                    continue 
                if mode not in options:
                    output.warning("You need to enter a valid function")
                    continue 
            except KeyboardInterrupt:
                print()
                output.info('Stopped action')
                pass 
        except KeyboardInterrupt:
            print()
            exit(0)
        except Exception as err:
            output.redd(str(err))

# run it     
asyncio.run(main())
