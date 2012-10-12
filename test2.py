from mpi4py import MPI

clusters = [0, 1, 2, 3, 4, 5, 6, 7, 8]

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank == 0: # only do it at processor 0 (root)
  broken_list = [list() for i in xrange(size)]

  for i, c in enumerate(clusters):
    broken_list[i % size].append(c)

  multiplier = (5, 4)
else:
  broken_list = None
  multiplier = None
#end if

my_clusters = comm.scatter(broken_list, root=0) # list of list, who is the parent
multiplier = comm.bcast(multiplier, root=0)

print '{} {} {}'.format(rank, multiplier, my_clusters)

for i, c in enumerate(my_clusters):
  my_clusters[i] = my_clusters[i] * multiplier[1]

gathered_clusters = comm.gather(my_clusters, root=0)

if rank == 0:
  print gathered_clusters
#end if