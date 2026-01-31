// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract InsuranceContract is Ownable, ReentrancyGuard {
    struct InsurancePolicy {
        uint256 coverageAmount;
        bool isActive;
    }

    mapping(address => InsurancePolicy) public policies;

    event PolicyPurchased(address indexed user, uint256 amount);
    event PayoutTriggered(address indexed user, uint256 amount);

    function purchasePolicy(uint256 coverageAmount) external payable nonReentrant {
        require(coverageAmount > 0, "Coverage amount must be greater than zero");
        policies[msg.sender] = InsurancePolicy({
            coverageAmount: coverageAmount,
            isActive: true
        });
        emit PolicyPurchased(msg.sender, coverageAmount);
    }

    function triggerPayout(address user) external onlyOwner {
        require(policies[user].isActive, "No active policy for this user");
        uint256 payoutAmount = policies[user].coverageAmount;
        policies[user] = InsurancePolicy({
            coverageAmount: 0,
            isActive: false
        });
        (bool sent, ) = user.call{value: payoutAmount}("");
        require(sent, "Failed to send Ether");
        emit PayoutTriggered(user, payoutAmount);
    }
}