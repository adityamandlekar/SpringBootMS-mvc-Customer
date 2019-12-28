package com.adim.springbootMS.web.controller;

import com.adim.springbootMS.services.CustomerService;
import com.adim.springbootMS.web.model.CustomerDto;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RequestMapping("/api/v1/customer")
@RestController
public class Customercontroller {

    private final CustomerService customerService;

    Customercontroller(CustomerService customerService) {
        this.customerService = customerService;
    }

    @GetMapping({"/{customerid}"})
    public ResponseEntity<CustomerDto> getCustomer(@PathVariable("customerid") UUID customerid) {
        return new ResponseEntity<>(customerService.getCutomerNamebyID(customerid), HttpStatus.OK);
    }

}
