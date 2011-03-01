#
# Cassandra Cluster Management lib
#

import os, common, shutil, re
from cluster import Cluster
from node import Node

USER_HOME = os.path.expanduser('~')

CASSANDRA_BIN_DIR= "bin"
CASSANDRA_CONF_DIR= "conf"

CASSANDRA_CONF = "cassandra.yaml"
LOG4J_CONF = "log4j-server.properties"
CASSANDRA_ENV = "cassandra-env.sh"
CASSANDRA_SH = "cassandra.in.sh"

class LoadError(Exception):
    pass

def get_default_path():
    default_path = os.path.join(USER_HOME, '.ccm')
    if not os.path.exists(default_path):
        os.mkdir(default_path)
    return default_path

def parse_interface(itf, default_port):
    i = itf.split(':')
    if len(i) == 1:
        return (i[0].strip(), default_port)
    elif len(i) == 2:
        return (i[0].strip(), int(i[1].strip()))
    else:
        raise ValueError("Invalid interface definition: " + itf)

def current_cluster_name(path):
    try:
        with open(os.path.join(path, 'CURRENT'), 'r') as f:
            return f.readline().strip()
    except IOError:
        return None

def load_current_cluster(path):
    name = current_cluster_name(path)
    if name is None:
        print 'No currently active cluster (use ccm cluster switch)'
        exit(1)
    try:
        return Cluster.load(path, name)
    except common.LoadError as e:
        print str(e)
        exit(1)

# may raise OSError if dir exists
def create_cluster(path, name):
    dir_name = os.path.join(path, name)
    os.mkdir(dir_name)
    cluster = Cluster(path, name)
    cluster.save()
    return cluster

def switch_cluster(path, new_name):
    with open(os.path.join(path, 'CURRENT'), 'w') as f:
        f.write(new_name + '\n')

def replace_in_file(file, regexp, replace):
    replaces_in_file(file, [(regexp, replace)])

def replaces_in_file(file, replacement_list):
    rs = [ (re.compile(regexp), repl) for (regexp, repl) in replacement_list]
    file_tmp = file + ".tmp"
    with open(file, 'r') as f:
        with open(file_tmp, 'w') as f_tmp:
            for line in f:
                for r, replace in rs:
                    match = r.search(line)
                    if match:
                        line = replace + "\n"
                f_tmp.write(line)
    shutil.move(file_tmp, file)

def make_cassandra_env(cassandra_dir, node_path):
    sh_file = os.path.join(CASSANDRA_BIN_DIR, CASSANDRA_SH)
    orig = os.path.join(cassandra_dir, sh_file)
    dst = os.path.join(node_path, sh_file)
    shutil.copy(orig, dst)
    replacements = [
        ('CASSANDRA_HOME=', '\tCASSANDRA_HOME=%s' % cassandra_dir),
        ('CASSANDRA_CONF=', '\tCASSANDRA_CONF=%s' % os.path.join(node_path, 'conf'))
    ]
    common.replaces_in_file(dst, replacements)
    env = os.environ.copy()
    env['CASSANDRA_INCLUDE'] = os.path.join(dst)
    return env