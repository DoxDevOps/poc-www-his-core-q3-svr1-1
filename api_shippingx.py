import logging
from typing import Any

import requests
import json
import platform
import subprocess
import os
from fabric import Connection


def get_data(url:str) -> Any:
    """
    Get data from service holding the site details

    This func has to explicitly know how the data is structure
    """

    try:
        response = requests.get(url)
        data = json.loads(response.text)
        data = data[0]['fields']
        return data
    
    except Exception as e:
        logging.debug("Couldn't get data from %s due to %s", url, e)
        return False    


def send_data(site:dict[str, Any], source:str, destination:str) -> bool:
    """Sends data to remote host"""

    try:
        send_data = f"rsync -r {source} {site['username']}@{site['ip_address']}:{destination}" 
        os.system(send_data)
        return True
    
    except Exception as e:
        logging.debug("Couldn't send data to %s due to %s", site['ip_address'], e)
        return False

def run_cmd_on_remote_host(site:dict[str, Any], cmd:str) -> Any:
    """Runs command on a remote host"""

    try:
        result = Connection(f"{site['username']}@{site['ip_address']}").run(cmd, hide=True)
        return "{0.stdout}".format(result).strip()
    
    except Exception as e:
        logging.debug("Failed to run %s on remote host %s because of error: %s", cmd, site["ip_address"], e)
        return False

def main():
    
    # [TODO] dynamically get cluster id
    cluster = get_data('http://10.44.0.52:8000/sites/api/v1/get_single_cluster/1')

    for site_id in cluster['site']:
        
        site = get_data(f'http://10.44.0.52:8000/sites/api/v1/get_single_site/{str(site_id)}')

        # functionality for ping re-tries
        # [TODO] use something like a decorator
        count = 0

        while (count < 3):

            # lets check if the site is available
            param = '-n' if platform.system().lower()=='windows' else '-c'

            if subprocess.call(['ping', param, '1', site['ip_address']]) == 0:
                
                # ship api to remote site
                send_data(site, "$WORKSPACE/BHT-EMR-API", "/var/www")
                
                # ship api script to remote site
                not send_data(site, "$WORKSPACE/api_setup.sh", "/var/www/BHT-EMR-API")

                # run setup script
                run_cmd_on_remote_host(site, "cd /var/www/BHT-EMR-API && ./api_setup.sh")
                
                # git describe
                run_cmd_on_remote_host(site, "cd /var/www/BHT-EMR-API && git describe")            
                           
                # close the while loop
                count = 3

            else:
                # increment the count
                count += 1              

if __name__ == '__main__':
    main()
        






