mark_as_advanced(ZMQPP_LIBRARY ZMQPP_INCLUDE_DIR)

find_path(ZMQPP_INCLUDE_DIR NAMES zmqpp.hpp PATH_SUFFIXES zmqpp)
message(${ZMQPP_INCLUDE_DIR})

find_library(ZMQPP_LIBRARY NAMES zmqpp)
message(${ZMQPP_LIBRARY})

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Zmqpp DEFAULT_MSG ZMQPP_LIBRARY ZMQPP_INCLUDE_DIR)
