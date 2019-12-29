package com.adim.springbootMS.services;

import com.adim.springbootMS.web.model.CustomerDto;

import java.util.UUID;

public interface CustomerService {

    CustomerDto getCutomerNamebyID(UUID uid);

    CustomerDto saveNewcustomer(CustomerDto customerDto);

    void updateCustomerbyID(UUID uuid, CustomerDto customerDto);

    void deleteCustomerbyID(UUID uuid);
}
