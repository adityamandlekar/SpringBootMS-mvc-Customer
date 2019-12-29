package com.adim.springbootMS.web.controller;

import com.adim.springbootMS.services.CustomerService;
import com.adim.springbootMS.web.model.CustomerDto;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

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

    @PostMapping
    public ResponseEntity handlePost(@RequestBody CustomerDto customerDto) {
        customerDto = customerService.saveNewcustomer(customerDto);
        HttpHeaders headers = new HttpHeaders();
        headers.add("Location", "http://localhost:8082/api/v1/customer/" + customerDto.getUid().toString());
        return new ResponseEntity(headers, HttpStatus.CREATED);

    }

    @PutMapping
    public ResponseEntity handleUpdate(UUID uuid, CustomerDto customerDto) {
        customerService.updateCustomerbyID(uuid, customerDto);
        return new ResponseEntity(HttpStatus.NO_CONTENT);
    }

    @DeleteMapping({"/{customerid}"})
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void DeletebyCustomerID(@PathVariable("customerid") UUID uuid) {
        customerService.deleteCustomerbyID(uuid);
    }
}
