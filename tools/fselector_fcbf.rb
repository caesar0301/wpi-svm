require 'fselector'

r1 = FSelector::FCBF.new
#r1.data_from_libsvm(fname="E:\\Documents\\Workspace\\pr-svm\\data\\normalized\\all.test.libsvm")

r1.data_from_libsvm(fname="E:\\Documents\\Workspace\\pr-svm\\libsvm\\tools\\fold1-test.libsvm")


# number of features before feature selection
puts "  # features (before): "+ r1.get_features.size.to_s

r1.select_feature!

# # number of features after feature selection
puts "  # features (after): "+ r1.get_features.size.to_s
puts r1.get_features.to_sym