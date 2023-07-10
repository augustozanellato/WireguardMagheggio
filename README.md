# WireguardMagheggio®

Quick and simple Wireguard-to-Wireguard router, useful during CTFs where only a limited number of VPN profiles are provided by the organizers.

## Prerequisites

- An [Hetzner](https://hetzner.cloud/?ref=qMnj59OBAqFn) account
- ansible
- A domain with DNS managed on Cloudflare

## Usage

1. Copy `config.sample.yml` to `config.yml` and edit as appropriate
1. Place one of the organizers-provided vpn profiles in `ctf.conf`, make sure to remove any `DNS =` entries because those break the playbook for an unknown reason.
1. `ansible-playbook playbooks/setup.yml`
1. Distribute to your teammates the profiles in `credentials/client`

### After CTF end

1. `ansible-playbook playbooks/teardown.yml`

## Misc notes

- TTL reset isn't done because ansible iptables module doesn't offer a clean way to do that
- `wg_generator.py` is kinda nice and reusable, you're free to ~~steal~~ use it
- I'm a total ansible n00b, you're free to shame me if you feel the need to do so

## Mandatory disclaimer

Stuff may break, your computer might explode and your Hetzner account could be used for mining if you run this playbook without ~~double~~ triple checking if everything looks good. No guarantees are provided etc etc _500 word of unreadable legalese were supposed to go here_.
