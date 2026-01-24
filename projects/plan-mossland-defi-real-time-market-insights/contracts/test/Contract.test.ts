import { expect } from "chai";
import { ethers } from "hardhat";

describe("Contract", function () {
  it("Should set the right name", async function () {
    const Contract = await ethers.getContractFactory("Contract");
    const contract = await Contract.deploy("Test");

    expect(await contract.name()).to.equal("Test");
  });
});
