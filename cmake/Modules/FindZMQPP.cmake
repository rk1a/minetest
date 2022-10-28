# Look for ZMQPP, with fallback to bundeled version
# Copied from FindJSON.cmake

# mark_as_advanced(JSON_LIBRARY JSON_INCLUDE_DIR)
# option(ENABLE_SYSTEM_JSONCPP "Enable using a system-wide JsonCpp" TRUE)
# set(USE_SYSTEM_JSONCPP FALSE)

# if(ENABLE_SYSTEM_JSONCPP)
# 	  find_library(JSON_LIBRARY NAMES jsoncpp)
#	  find_path(JSON_INCLUDE_DIR json/allocator.h PATH_SUFFIXES jsoncpp)
#
#	  if(JSON_LIBRARY AND JSON_INCLUDE_DIR)
#		  message(STATUS "Using JsonCpp provided by system.")
#		  set(USE_SYSTEM_JSONCPP TRUE)
#	  endif()
#  endif()

#  if(NOT USE_SYSTEM_JSONCPP)
if(ZEROMQ_INCLUDE)
    if(ZEROMQ_LIBRARY_SHARED OR ZEROMQ_LIBRARY_STATIC)
        message(STATUS "Using bundled ZeroMQ library.")
        set(ZMQPP_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/lib/zmqpp)
        set(ZMQPP_LIBRARY zmqpp)
        add_subdirectory(lib/zmqpp)

        include(FindPackageHandleStandardArgs)
        find_package_handle_standard_args(ZMQPP DEFAULT_MSG ZMQPP_LIBRARY ZMQPP_INCLUDE_DIR)
    endif()
endif()
#  endif()
